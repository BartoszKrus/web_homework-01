from collections import UserDict
from datetime import datetime, timedelta
import pickle
import re
import shutil
import os
import zipfile
import tarfile
import gzip
from pathlib import Path


POLISH_LETTERS = {'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n', 'ó': 'o', 'ś': 's', 'ż': 'z', 'ź': 'z'}

IMAGE_EXTENSIONS = ['JPEG', 'PNG', 'JPG', 'SVG']
VIDEO_EXTENSIONS = ['AVI', 'MP4', 'MOV', 'MKV', 'GIF']
DOCUMENTS_EXTENSIONS = ['DOC', 'DOCX', 'TXT', 'PDF', 'XLSX', 'PPTX', 'PY']
AUDIO_EXTENSIONS = ['MP3', 'OGG', 'WAV', 'AMR']
APLICATIONS_EXTENSIONS = ['EXE']
ARCHIVES_EXTENSIONS = ['ZIP', 'GZ', 'TAR']


class Field:
    def __init__(self, value=None):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    def __init__(self, name):
        super().__init__(name)


class Phone(Field):
    def __init__(self, phone):
        normalized_phone = ''.join(filter(str.isdigit, str(phone)))
        if len(normalized_phone) == 9:
            phone = normalized_phone
        else:
            raise ValueError("Phone number must contain exactly 9 digits.")
        super().__init__(phone)


class Birthday(Field):
    def __init__(self, birthday=None):
        if birthday is not None:
            try:
                birthday = datetime.strptime(birthday, "%d-%m-%Y")
            except ValueError:
                raise ValueError("Birthday must be in 'dd-mm-yyyy' format.")
        super().__init__(birthday)


class Address(Field):
    def __init__(self, value=None):
        self.value = value


class Email(Field):
    def __init__(self, email):
        if email is not None:
            check = re.findall(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+', email)
            if len(check) == 1:
                self.value = email
            else:
                raise ValueError('Incorrect email address')
        else:
            self.value = None


class Tag(Field):
    def __init__(self, value=None):
        self.value = value


class Note(Field):
    def __init__(self, value=None):
        self.value = value


class Record:
    def __init__(self, name, birthday=None, address=None, email=None):
        self.name = Name(name)
        self.birthday = Birthday(birthday)
        self.phones = []
        self.note = {}
        self.address = address
        self.email = email

    def add_phone(self, phone):
        self.phones.append(phone)



    def remove_phone(self, phone):
        phone_to_remove = str(phone)
        if phone_to_remove in [str(p) for p in self.phones]:
            self.phones = [p for p in self.phones if str(p) != phone_to_remove]

    def edit_phone(self, old_phone, new_phone):
        old_phone_obj = Phone(old_phone)
        for i, phone in enumerate(self.phones):
            if str(phone) == str(old_phone_obj):
                self.phones[i] = Phone(new_phone)
                return
        print("Old phone number not found.")

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def remove_birthday(self):
        self.birthday = Birthday()

    def add_address(self, address):
        self.address = Address(address)

    def edit_address(self, new_address):
        self.address = Address(new_address)

    def remove_address(self):
        self.address = Address()

    def add_email(self, email):
        while True:  # Pętla będzie kontynuowana dopóki nie zostanie wprowadzony poprawny email
            try:
                self.email = Email(email)
                break  # Jeśli email jest poprawny, przerywamy pętlę
            except ValueError:
                print("Invalid email address. Please try again. If you don't want to add email address just press enter")
                email = input("If you don't want to add email address just press enter./nEnter email (example@dummy.com): ")
                if not email.strip():
                    break

    def days_to_birthday(self):
        if self.birthday.value is None:
            return None
        now = datetime.now()
        next_birthday = datetime(now.year, self.birthday.value.month, self.birthday.value.day)
        if now > next_birthday:
            next_birthday = datetime(now.year + 1, self.birthday.value.month, self.birthday.value.day)
        return (next_birthday - now).days

    def add_note(self, tag, new_note):
        self.note[tag] = new_note

    def remove_note(self, tag):
        if tag in self.note:
            del self.note[tag]
            print(f"Success:  note with tag {tag} has been removed successfully. \n")


    def edit_note(self, tag, new_note):
        if tag in self.note:
            self.note[tag] = new_note

    def __str__(self):
        return f"Name: {self.name}, Phones: {', '.join(map(str, self.phones))}, Birthday: {self.birthday}, Email: {self.email}, Address: {self.address}, Notes: {', '.join(f'({tag}) {note}' for tag, note in self.note.items())}"


class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find_records(self, keyword):
        results = []
        keyword_lower = keyword.lower()
        for record in self.data.values():
            if keyword_lower == record.name.value.lower():
                results.append(record)
            else:
                for phone in record.phones:
                    if keyword_lower == str(phone).lower():
                        results.append(record)
                        break  
        return results

    def find_partial_records(self, keyword):
        results = []
        keyword_lower = keyword.lower()
        for record in self.data.values():
            if keyword_lower in record.name.value.lower() or any(keyword_lower in str(phone).lower() for phone in record.phones):
                results.append(record)
        return results

    def phone_exists(self, name, phone):
        existing_records = self.find_records(name)
        if existing_records:
            record = existing_records[0]
            return str(phone) in [str(phone_obj) for phone_obj in record.phones]
        return False

    def upcoming_birthdays(self, days):
        upcoming_bdays = []
        today = datetime.now().date()
        for record in self.data.values():
            if record.birthday.value:
                bday_this_year = datetime(today.year, record.birthday.value.month, record.birthday.value.day).date()
                if (bday_this_year - today).days <= days:
                    upcoming_bdays.append(record)
        return upcoming_bdays

    def __iter__(self):
        self._current = 0
        self._records = list(self.data.values())
        return self

    def __next__(self):
        if self._current >= len(self._records):
            raise StopIteration
        result = self._records[self._current]
        self._current += 1
        return result

    def save_to_file(self, filename):
        home_folder = os.path.expanduser("~")
        file_path = os.path.join(home_folder, filename)
        
        with open(file_path, 'wb') as fh:
            pickle.dump(self, fh)

    def load_from_file(filename):
        home_folder = os.path.expanduser("~")
        file_path = os.path.join(home_folder, filename)
        
        with open(file_path, 'rb') as fh:
            content = pickle.load(fh)
        return content

    def search_and_sort_notes_by_tag(self, tag):
        records_with_tag = []
        for record in self.data.values():
            if tag in record.note:
                records_with_tag.append(record)

        records_with_tag.sort(key=lambda x: x.note[tag])
        return records_with_tag


class CleanFolder:
    def __init__(self, path):
        self.path = path
        self.all_existing_extentions = set()
        self.unrecognized_extensions = set()



    def normalize(self, some_string):  
        result = ""
        for char in some_string:
            if char.lower() in POLISH_LETTERS:
                result += POLISH_LETTERS[char.lower()]
            elif char.isspace() or char.isalnum():
                result += char
            else:
                result += "_"
        return result 

    def move_and_normalize_files(self, file_path, new_folder_name):
        normalized_name = self.normalize(Path(file_path).stem)
        move_file = os.path.join(os.path.dirname(file_path), new_folder_name)
        move_to = os.path.join(move_file, f"{normalized_name}.{file_path.split('.')[-1]}")

        os.makedirs(move_file, exist_ok= True)
        shutil.move(file_path, move_to)

    def archive_folder_and_move(self, path, arch_name, new_folder_name):
        arch_path = os.path.join(path, arch_name)
        extracted_archive = os.path.join(path, arch_name.split('.')[0])
        move_file = os.path.join(os.path.dirname(arch_path), new_folder_name)
        move_to = os.path.join(move_file, arch_name.split('.')[0])

        if arch_name.split('.')[-1].upper() == 'ZIP':
            with zipfile.ZipFile(arch_path, 'r') as zip:
                zip.extractall(extracted_archive)

        elif arch_name.split('.')[-1].upper() == 'TAR':
            with tarfile.open(arch_path, 'r') as tar:
                tar.extractall(extracted_archive)

        elif arch_name.split('.')[-1].upper() == 'GZ':
            with gzip.open(arch_path, 'rb') as f_in, open(extracted_archive, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        os.remove(arch_path)
        os.makedirs(move_file, exist_ok = True)
        shutil.move(extracted_archive, move_to)      

    def process_folder(self):
        for root, dirs, files in os.walk(self.path):

            for file in files:
                file_path = os.path.join(root, file)
                extension = file.split('.')[-1].upper()


                if any(folder in root for folder in ["Pictures", "Video", "Documents", "Music", "Aplications", "Unrecognized extensions"]):
                    continue
                if extension in IMAGE_EXTENSIONS:
                    self.all_existing_extentions.add(extension)
                    self.move_and_normalize_files(file_path, "Pictures")
                elif extension in VIDEO_EXTENSIONS:
                    self.all_existing_extentions.add(extension)
                    self.move_and_normalize_files(file_path, "Video")
                elif extension in DOCUMENTS_EXTENSIONS:
                    self.all_existing_extentions.add(extension)
                    self.move_and_normalize_files(file_path, "Documents")
                elif extension in AUDIO_EXTENSIONS:
                    self.all_existing_extentions.add(extension)
                    self.move_and_normalize_files(file_path, "Music")
                elif extension in APLICATIONS_EXTENSIONS:
                    self.all_existing_extentions.add(extension)
                    self.move_and_normalize_files(file_path, "Aplications")
                elif extension in ARCHIVES_EXTENSIONS:
                    self.all_existing_extentions.add(extension)
                    self.archive_folder_and_move(root, file, "Archive")
                else:
                    self.unrecognized_extensions.add(extension)
                    continue

            for dir in dirs:
                dir_path = os.path.join(root, dir)
                new_dir_path = os.path.join(root, self.normalize(dir))
                if not os.listdir(dir_path):
                    os.rmdir(dir_path)
                else:
                    os.rename(dir_path ,new_dir_path)
        print(self.all_existing_extentions)
        print(self.unrecognized_extensions)


def main():
    """
    The main() function is responsible for managing user interaction with the phone book.
    Users can perform various operations on entries in the phone book, such as adding,
    editing, removing, searching, and displaying entries, and calculating the number of 
    days to birthdays. The phonebook can be saved as well as loaded after restarting the 
    program.

    Commands:
    - '.' - End the program.
    - 'good bye', 'close', 'exit' - Terminate the program with the message "Good bye!".
    - 'hello' - Display a greeting.
    - 'add' - Add a new entry to the address book.
    - 'add phone' - Add a new phone number to an existing entry.
    - 'edit phone' - Edit an existing phone number.
    - 'remove phone' - Remove a phone number from an existing entry.
    - 'add address' - Adding address to an existing entry.
    - 'edit address' - Editing address of an existing entry.
    - 'remove address' - Removing address of an existing entry.
    - 'add birthday' - Add a birthday to an existing entry.
    - 'remove birthday' - Remove the birthday from an existing entry.
    - 'add email' - Add an email address to en existing entry.
    - 'edit email' - Edit email of an existing entry
    - 'add note' - adds a new note with tag to contact.
    - 'remove note' - removes a note from contact.
    - 'edit note' - edits a note in contact.
    - 'clean' - sorts files in chosen folder by file type.
    - 'find' - Search for entries in the address book.
    - 'days to birthday' - Calculate the number of days until the next birthday.
    - 'upcoming birthdays' - Displays a list of contacts whose birthdays are a specified number of days from the current date;
    - 'show all' - Display all entries in the address book.
    - 'save' - Save the address book to a file.
    - 'load address book' - Load the address book from a file.
    - 'search and sort notes' - Search and sort notes by a specific tag.
    """
    address_book = AddressBook()

    while True:
        command = input("Enter command: ").lower()

        if '.' in command:
            break

        elif command in ['good bye', 'close', 'exit']:
            print("Good bye!")
            break

        elif command == "hello":
            print("How can I help you?")

        elif command == "add":
            name = input("Enter name: ")
            if not name.strip():
                print("Error: Name cannot be empty.\n")
                continue

            existing_records = address_book.find_records(name)
            if existing_records:
                print(f"Error: This name: {name} already exists in the address book. Please choose a different name.\n")
                continue

            else:
                record = Record(name)                
                phone = input("Enter phone number: ")
                phone_str = ''
                if phone.strip():
                    try:
                        phone = Phone(phone)
                        record.add_phone(phone)
                        phone_str = phone
                    except ValueError as e:
                        print(f"Incorrect phone number: {e}")

                birthday = input("Enter birthday (dd-mm-yyyy): ")
                birthday_str = ''
                if birthday.strip():
                    try:
                        record.add_birthday(birthday)
                        birthday_str = birthday
                    except ValueError as e:
                        print(f"Incorrect birthday format: {e}")

                email = input("If you don't want to add email address just press enter. \nEnter email (example@dummy.com):")
                email_str = ''
                if email.strip():
                    try:
                        record.add_email(email)
                        email_str = email
                    except ValueError:
                        print('Invalid email address')
                address_book.add_record(record)

                tag = input("Enter tag: ")
                note = input("Enter note: ")
                record.add_note(tag, note)


            print(f"Success: Record: \n Name: {name} \n Numbers: {phone_str}\n Birthday: {birthday_str}\n Email: {record.email}\n Address: {record.address}\n Note: ({tag}) {note} \nhas been added successfully. \n added successfully.")

        elif command == "add phone":
            name = input("Enter name phone: ")
            if not name.strip():
                print("Error: Name cannot be empty. Please enter a valid name.\n")
                continue

            existing_records = address_book.find_records(name)
            if not existing_records:
                print(f"Error: This name: {name} does not exist in the address book. Please add a new record first.\n")
            else:
                phone = input("Enter phone number: ")
                if phone.strip():
                    try:
                        phone = Phone(phone)
                        record = existing_records[0]
                        record.add_phone(phone)
                        print(f"Success: Phone number: {phone} added successfully to {name}.\n")
                    except ValueError as e:
                        print(f"Incorrect phone number: {e}")
                else:
                    print("Error: No phone number was provided. No new number added.\n")

        elif command == 'add email':
            name = input("Enter name phone: ")
            if not name.strip():
                print("Error: Name cannot be empty. Please enter a valid name.\n")
                continue

            existing_records = address_book.find_records(name)
            if not existing_records:
                print(f"Error: This name: {name} does not exist in the address book. Please add a new record first.\n")

            else:
                email = input('Enter email address: ')
                if email.strip():
                    record = existing_records[0]
                    new_email = Email(email)
                    record.add_email(new_email)

        elif command == 'add address':
            name = input('Enter name: ')
            if not name.strip():
                print("Error: Name cannot be empty. Please enter a valid name.\n")
                continue
            existing_records = address_book.find_records(name)
            if not existing_records:
                print(f"Error: This name: {name} does not exist in the address book. Please add a new record first.\n")
            else:
                record = existing_records[0]
                address = input('Enter address: ')
                new_address = Address(address)
                record.add_address(new_address)
                print(f"Address added successfully to {name}.\n")

        elif command == "edit address":
            name = input("Enter name to edit address: ")
            if not name.strip():
                print("Error: Name cannot be empty. Please enter a valid name.\n")
                continue
            existing_records = address_book.find_records(name)
            if existing_records:
                record = existing_records[0]
                new_address = input("Enter new address: ")
                record.edit_address(new_address)
                print(f"Success: Address updated successfully for {name}.\n")
            else:
                print(f"Error: Name: {name} not found in the address book.\n")

        elif command == "remove address":
            name = input("Enter name to remove address: ")
            if not name.strip():
                print("Error: Name cannot be empty. Please enter a valid name.\n")
                continue
            existing_records = address_book.find_records(name)
            if existing_records:
                record = existing_records[0]
                record.remove_address()
                print(f"Success: Address removed successfully for {name}.\n")
            else:
                print(f"Error: Name: {name} not found in the address book.\n")


        elif command == "edit phone":
            name = input("Enter name to edit phone number: ")
            if not name.strip():
                print("Error: Name cannot be empty. Please enter a valid name.\n")
                continue

            results = address_book.find_records(name)
            if results:
                record = results[0]
                phone = input("Enter new phone number: ")
                if phone.strip():
                    try:
                        phone = Phone(phone)
                        old_phone = input("Enter old phone number to replace: ")
                        old_phone = Phone(old_phone)
                        if str(old_phone) in [str(phone_obj) for phone_obj in record.phones]:
                            record.edit_phone(old_phone, phone)
                            print(f"Success: Phone number: {phone} updated successfully.\n")
                        else:
                            print(f"Error: Old phone number: {old_phone} not found for {name}.\n")
                    except ValueError as e:
                        print(f"Incorrect phone number: {e}")
                else:
                    print(f"Error: New phone number not provided.\n")                    
            else:
                print(f"Error: Name: {name} not found in the address book.\n")

        elif command == "edit email":
            name = input("Enter email name: ")

            if not name.strip():
                print("Error: Name cannot be empty. Please enter a valid name.\n")
                continue

            results = address_book.find_records(name)
            if results:
                record = results[0]
                email = input('Enter new email: ')
                new_email = Email(email)
                record.add_email(str(new_email))
                print('done', record.email)

        elif command == "find":
            search_char = input("Enter the character by which you want to search for users: ").strip().lower()
            if not search_char:
                print("Error: The character you searched for cannot be empty.\n")
                continue

            results = address_book.find_partial_records(search_char)
            if results:
                print("Success: Records found:")
                N = 5
                for i in range(0, len(results), N):
                    for record in results[i:i+N]:
                        print(record)
                    if i + N < len(results):
                        input("Press enter to see the next page...\n")
            else:
                print("Error: No matching records found.")


        elif command == "add birthday":
            name = input("Enter name: ")
            if not name.strip():
                print("Error: Name cannot be empty. Please enter a valid name.\n")
                continue

            existing_records = address_book.find_records(name)
            if existing_records:
                record = existing_records[0]
                if record.birthday.value is None:
                    birthday = input("Enter birthday (dd-mm-yyyy): ")
                    if birthday.strip():
                        try:
                            record.add_birthday(birthday)
                            print(f"Success: Birthday: {birthday} added successfully to {name}.\n")
                        except ValueError as e:
                            print(f"Incorrect birthday format: {e}")
                    else:
                        print("Error: No birthday was provided. No new birthday added.\n")
                else:
                    print(f"Error: A birthday is already assigned to {name}. Cannot add more than one birthday.\n")
            else:
                print(f"Error: Name: {name} not found in the address book.\n")



        elif command == "remove birthday":
            name = input("Enter name to remove birthday: ")
            if not name.strip():
                print("Error: Name cannot be empty. Please enter a valid name.\n")
                continue

            existing_records = address_book.find_records(name)
            if existing_records:
                record = existing_records[0]
                if record.birthday.value is not None:
                    record.remove_birthday()
                    print(f"Success: Birthday removed successfully for {name}.\n")
                else:
                    print(f"Error: No birthday found for {name}.\n")
            else:
                print(f"Error: Name: {name} not found in the address book.\n")

        elif command == "add note":
            name = input("Enter name: ")
            if not name.strip():
                print("Error: Name cannot be empty. Please enter a valid name.\n")

            else:
                records = address_book.find_records(name)
                if records:
                    record = records[0]
                    tag = input("Enter tag: ")    
                    note = input("Enter note: ")
                    record.add_note(tag, note)
                    print(f"Success:  note: ({tag}) {note} has been added successfully. \n")
                else:
                    print(f"Error: Name: {name} not found in the address book.\n")
        
        elif command == "search and sort notes":
            tag = input("Enter the tag to search and sort by: ")
            tagged_records = address_book.search_and_sort_notes_by_tag(tag)
            if tagged_records:
                print(f"Success: Records with tag '{tag}':")
                for record in tagged_records:
                    print(record)
                print('')
            else:
                print(f"No records found with tag '{tag}'.\n")            

        elif command == "remove note":
            name = input("Enter name: ")
            if not name.strip():
                print("Error: Name cannot be empty. Please enter a valid name.\n")   
            else:
                records = address_book.find_records(name)
                if records:
                    record = records[0]
                    tag = input("Enter tag: ")
                    record.remove_note(tag)
                else:
                    print(f"Error: No record found for {name}.\n")

        elif command == "edit note":
            name = input("Enter name: ")
            if not name.strip():
                print("Error: Name cannot be empty. Please enter a valid name.\n")
                continue

            else:
                records = address_book.find_records(name)
                if records:
                    record = records[0]
                    if record:
                        print("Do you wish to also change a tag? \n")
                        valid = input("(y/n): ")
                        if valid == "y":
                            tag = input("Enter old tag: ")
                            new_tag = input("Enter new tag: ")
                            new_note = input("Enter new note: ")
                            record.remove_note(tag)
                            record.add_note(new_tag, new_note)

                        elif valid == "n":  
                            tag = input("Enter tag: ")
                            new_note = input("Enter note: ")
                            record.edit_note(tag, new_note)
                            print(f"Success:  note in {name} with tag {tag} has been edited successfully. \n")
                    else:
                        print(f"Error: Name: {name} not found in the address book.\n")

        elif command == "clean":
            path = input("Enter Path to folder:")
            cleanfolder = CleanFolder(path)
            try:
                cleanfolder.process_folder()
            except TypeError:
                print("Error: Chosen path is incorrect.")

        elif command == "days to birthday":
            name = input("Enter name: ")
            if not name.strip():
                print("Error: Name cannot be empty. Please enter a valid name.\n")
                continue

            existing_records = address_book.find_records(name)
            if existing_records:
                record = existing_records[0]
                days = record.days_to_birthday()
                if days is not None:
                    print(f"Success: There are {days} days until {name}'s next birthday.\n")
                else:
                    print(f"Error: No birthday found for {name}.\n")
            else:
                print(f"Error: Name: {name} not found in the address book.\n")


        elif command == "upcoming birthdays":
            try:
                days = int(input("Enter the number of days to search for upcoming birthdays: "))
                if days < 0:
                    print("Error: Please enter a non-negative number of days.\n")
                    continue
                today = datetime.now().date()
                upcoming_bdays = address_book.upcoming_birthdays(days)
                if days == 0:
                    upcoming_bdays_today = [record for record in upcoming_bdays if datetime(today.year, record.birthday.value.month, record.birthday.value.day).date() == today]
                    if upcoming_bdays_today:
                        print(f"Success: Found contacts with birthdays today:")
                        for record in upcoming_bdays_today:
                            print(record)
                        print('')
                    else:
                        print("No upcoming birthdays found for today.\n")
                else:
                    upcoming_bdays_future = [record for record in upcoming_bdays if (record.birthday.value.month > today.month) or (record.birthday.value.month == today.month and record.birthday.value.day >= today.day)]
                    if upcoming_bdays_future:
                        print(f"Success: Found contacts with upcoming birthdays within {days} days:")
                        for record in upcoming_bdays_future:
                            print(record)
                        print('')
                    else:
                        print("No upcoming birthdays found.\n")
            except ValueError:
                print("Error: Please enter a valid number of days for upcoming birthdays search.\n")


        elif command == "show all":
            if address_book:
                print("Success: All Contacts:")
                N = 5
                records = list(address_book.data.values())
                for i in range(0, len(records), N):
                    for record in records[i:i+N]:
                        print(record)
                    if i + N < len(records):
                        input("Press enter to see the next page...\n")
                print()
            else:
                print("Error: Address book is empty.\n")


        elif command == "save":
            filename = input("Enter the filename to save the address book: ")
            address_book.save_to_file(filename)
            print(f"Success: Address book saved to {filename}.\n")


        elif command == "load address book":
            filename = input("Enter the filename to load the address book from: ")
            try:
                address_book = AddressBook.load_from_file(filename)
                print(f"Success: Address book loaded from {filename}.\n")
            except FileNotFoundError:
                print(f"Error: File {filename} not found.\n")


        else:
            print("Error: Invalid command. Enter the correct command.\n")

if __name__ == "__main__":
    main()