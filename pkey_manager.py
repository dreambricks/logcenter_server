import os
import re


class PKeyManager:
    def __init__(self, directory):
        self.directory = directory
        self.files = self._load_files()

    def _load_files(self):
        """Load .pem files that match the pattern nnn.pem into a dictionary."""
        pem_files = {}
        pattern = re.compile(r"(\d{3})\.pem$")  # Match files like 001.pem, 123.pem

        for filename in os.listdir(self.directory):
            match = pattern.match(filename)
            if match:
                key = int(match.group(1))  # Extract numeric part
                with open(os.path.join(self.directory, filename), "r", encoding="utf-8") as file:
                    pem_files[key] = file.read()

        return pem_files

    def get_count(self):
        """Return the number of items in the dictionary."""
        return len(self.files)

    def get_content(self, key):
        """Return the content of a file for a given key (nnn as a string)."""
        return self.files.get(key, None)


if __name__ == '__main__':
    # Example usage:
    reader = PKeyManager("pkeys")
    print(reader.get_count())  # Number of files loaded
    print(reader.get_content(0))  # Content of 000.pem
