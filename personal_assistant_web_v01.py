from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import re


class DisplayStrategy(ABC):
    @abstractmethod
    def display(self, record):
        pass

class ConsoleDisplayStrategy(DisplayStrategy):
    def display(self, record):
        print("Name:", record.name)
        print("Phone:", ', '.join([str(phone.get_value()) for phone in record.phone.phones]))
        print("Birthday:", record.birthday.birthday.get_value())
        print("Address:", record.address.address.get_value())
        print("Email:", record.email.email.get_value())
        print("Info:")
        for key, value in record.info.notes.items():
            print(f"{key.get_value()} -> {value.get_value()}")
        print("\n")


class Validator(ABC):
    @abstractmethod
    def validate(self, value):
        pass


class PhoneValidator(Validator):
    def validate(self, value):
        if not value.isdigit():
            raise ValueError("The phone number must contain only digits.")
        if len(value) != 9:
            raise ValueError("Phone number must contain exactly 9 digits.")
        

class DateValidator(Validator):
    def validate(self, value):
        try:
            datetime.strptime(value, "%d-%m-%Y")
        except ValueError:
            raise ValueError("Birthday must be in 'dd-mm-yyyy' format.")
        

class EmailValidator(Validator):
    def validate(self, value):
        if value is not None:
            check = re.findall(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+', value)
            if len(check) == 1:
                self.value = value
            else:
                raise ValueError('Incorrect email address')
        else:
            self.value = None
        

class Field:
    def __init__(self, value=None, validator=None):
        self.value = value
        self.validator = validator

    def set_value(self, value):
        if self.validator:
            self.validator.validate(value)
        self.value = value

    def get_value(self):
        return self.value
    

class RecordPhone:
    def __init__(self, phone=None, phones=None):
        self.phone = Field(phone, PhoneValidator())
        self.phones = phones if phones else []

    def add_phone(self, phone):
        new_phone = Field(validator=PhoneValidator())
        new_phone.set_value(phone)
        self.phones.append(new_phone)

    def remove_phone(self, phone):
        phone_to_remove = str(phone)
        if phone_to_remove in [str(p.get_value()) for p in self.phones]:
            self.phones = [p for p in self.phones if str(p.get_value()) != phone_to_remove]

    def edit_phone(self, old_phone, new_phone):
        old_phone_obj = Field(old_phone)
        for i, phone in enumerate(self.phones):
            if str(phone.get_value()) == str(old_phone_obj.get_value()):
                self.phones[i] = Field(new_phone, PhoneValidator())
                return
        print("Old phone number not found.")


class RecordBirthday:
    def __init__(self, birthday=None):
        self.birthday = Field(birthday, DateValidator())

    def add_birthday(self, birthday):
        self.birthday.set_value(birthday)

    def edit_birthday(self, new_birthday):
        self.birthday.set_value(new_birthday)

    def remove_birthday(self):
        self.birthday.set_value(None)

    def days_to_birthday(self):
        if self.birthday.get_value():
            today = datetime.today()
            birthday_date = datetime.strptime(self.birthday.get_value(), '%d-%m-%Y')
            next_birthday = datetime(today.year, birthday_date.month, birthday_date.day)
            if today > next_birthday:
                next_birthday = datetime(today.year + 1, birthday_date.month, birthday_date.day)
            delta = next_birthday - today
            return delta.days
        else:
            return None
        

class RecordAddress:
    def __init__(self, address=None):
        self.address = Field(address)

    def add_address(self, address):
        self.address.set_value(address)

    def edit_address(self, new_address):
        self.address.set_value(new_address)

    def remove_address(self):
        self.address.set_value(None)


class RecordEmail:
    def __init__(self, email=None):
        self.email = Field(email, EmailValidator())
        
    def add_email(self, email):
        self.email.set_value(email)

    def edit_email(self, new_email):
        self.email.set_value(new_email)

    def remove_email(self):
        self.email.set_value(None)   
    

class RecordInfo:
    def __init__(self, tag=None, note=None, notes=None):
        self.tag = Field(tag)
        self.note = Field(note)
        self.notes = notes if notes else {}

    def add_note(self, tag, note):
        self.notes[Field(tag)] = Field(note)

    def edit_note(self, tag, new_note):
        if tag in self.notes:
            self.notes[tag].set_value(new_note)
        else:
            print("Note with this tag does not exist.")

    def remove_note(self, tag):
        if tag in self.notes:
            del self.notes[tag]
            print(f"Success:  note with tag {tag} has been removed successfully. \n")
        else:
            print(f"Note with tag {tag} does not exist.")


class Record:
    def __init__(self, name):
        self.name = name
        self.phone = RecordPhone()
        self.birthday = RecordBirthday()
        self.address = RecordAddress()
        self.email = RecordEmail()
        self.info = RecordInfo()

    def display(self, display_strategy):
        display_strategy.display(self)


class AddressBook:
    def __init__(self):
        self.records = []

    def add_record(self, record):
        self.records.append(record)

    def display_all(self, display_strategy):
        for record in self.records:
            record.display(display_strategy)


if __name__ == "__main__":
    address_book = AddressBook()
    record1 = Record("John Doe")
    record1.phone.add_phone("123456789")
    record1.phone.add_phone("123456789")
    record1.phone.add_phone("123456789")
    record1.phone.add_phone("123456789")
    record1.birthday.add_birthday("15-05-1990")
    record1.info.add_note("Rodzina", "Mam żonę.")
    record1.info.add_note("Zwierzęta", "Mam dwa psy i jednego kota.")
    record1.address.add_address("ul. Zachlapana 13, 01-200 Warszawa")
    record1.email.add_email("john.doe@gmail.com")

    record2 = Record("Jane Smith")
    record2.phone.add_phone("987654321")
    record2.birthday.add_birthday("30-11-1988")

    record3 = Record("Alice Wonderland")
    record3.phone.add_phone("555888777")
    record3.birthday.add_birthday("20-03-1995")

    address_book.add_record(record1)
    address_book.add_record(record2)
    address_book.add_record(record3)

    print("\n")
    
    console_display_strategy = ConsoleDisplayStrategy()

    address_book.display_all(console_display_strategy)
