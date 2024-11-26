import os
import csv
import time
import requests
import logging

class LogDataUploader:
    def __init__(self, output_folder, upload_url, check_interval_seconds):
        self.output_folder = output_folder
        self.upload_url = upload_url
        self.check_interval_seconds = check_interval_seconds

        self.datalog_folder = os.path.join(os.getcwd(), self.output_folder)
        self.output_path = self.ensure_csv_file_exists("data_logs.csv")
        self.backup_path = self.ensure_csv_file_exists("data_logs_backup.csv")

        # Configuração do logger
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                logging.FileHandler("uploader.log"),
                logging.StreamHandler()
            ]
        )

    def ensure_directory_exists(self, directory):
        if not os.path.exists(directory):
            os.makedirs(directory)

    def ensure_csv_file_exists(self, file_name):
        self.ensure_directory_exists(self.datalog_folder)
        file_path = os.path.join(self.datalog_folder, file_name)
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                writer = csv.writer(f)
                writer.writerow(["timePlayed", "status", "project", "additional"])  # Adding headers
        return file_path

    def check_internet_connection(self):
        try:
            requests.get("https://www.google.com", timeout=5)
            return True
        except requests.ConnectionError:
            return False

    def worker(self):
        while True:
            time.sleep(self.check_interval_seconds)

            if not self.check_internet_connection():
                logging.warning("No internet available")
                continue

            if os.path.exists(self.output_path):
                # Lê todas as linhas do arquivo CSV
                with open(self.output_path, 'r') as csv_file:
                    reader = list(csv.reader(csv_file))
                    header = reader[0]  # Cabeçalho
                    lines = reader[1:]  # Dados, excluindo o cabeçalho

                if not lines:
                    logging.info(f"The CSV file is empty: {self.output_path}")
                    continue

                updated_lines = lines[:]  # Copia todas as linhas de dados
                for i, line in enumerate(lines):  # Itera pelas linhas originais
                    send_success = self.send_data(line)

                    if send_success:
                        # Escreve a linha enviada no arquivo de backup
                        with open(self.backup_path, 'a', newline='') as backup_file:
                            writer = csv.writer(backup_file)
                            writer.writerow(line)

                        # Remove a linha da lista de linhas atualizadas
                        updated_lines.remove(line)

                # Reescreve o arquivo original apenas com as linhas restantes
                with open(self.output_path, 'w', newline='') as csv_file:
                    writer = csv.writer(csv_file)
                    writer.writerow(header)  # Reescreve o cabeçalho
                    writer.writerows(updated_lines)  # Reescreve as linhas restantes

    def send_data(self, line):
        data = {
            "timePlayed": line[0],
            "status": line[1],
            "project": line[2],
            "additional": line[3],
        }

        try:
            response = requests.post(self.upload_url, data=data)
            if response.status_code == 200:
                logging.info(f"Successfully uploaded line: {line}")
                return True
            else:
                logging.error(f"Failed to upload line: {line}. Response: {response.status_code}")
                return False
        except Exception as e:
            logging.error(f"Error while uploading line: {line}. Error: {str(e)}")
            return False

if __name__ == "__main__":
    uploader = LogDataUploader(
        output_folder="data_logs",
        upload_url="http://18.229.132.107:5000/datalog/upload",
        check_interval_seconds=5
    )
    uploader.worker()
