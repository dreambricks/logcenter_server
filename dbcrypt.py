import base64
import os
import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes

# Definição de constantes
MAX_BLOCK_LENGTH = 122
AES_KEY_LENGTH = 32
AES_IV_LENGTH = 16


def db_generate_rsa_keys():
    """Gera um par de chaves RSA"""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=1024
    )
    public_key = private_key.public_key()

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    return {
        "public_key": public_pem.decode('utf-8'),
        "private_key": private_pem.decode('utf-8')
    }


def db_generate_aes_keys():
    """Gera uma chave AES e IV"""
    passphrase = db_generate_passphrase()
    key = hashlib.sha256(passphrase.encode()).digest()
    iv = key[:AES_IV_LENGTH]
    return {
        "key": key,
        "iv": iv
    }


def db_encrypt_byte(data, public_pem):
    """Criptografa bytes usando RSA ou combinação RSA + AES"""
    if len(data) <= MAX_BLOCK_LENGTH:
        encrypted_data = db_encrypt_rsa(data, public_pem)
        return b'0' + encrypted_data  # Prefixo '0' indica criptografia apenas RSA

    aes_keys = db_generate_aes_keys()
    encrypted_data = db_encrypt_aes(data, aes_keys["key"], aes_keys["iv"])

    encrypted_aes_key = db_encrypt_rsa(aes_keys["key"], public_pem)
    encrypted_aes_iv = db_encrypt_rsa(aes_keys["iv"], public_pem)

    return b'1' + encrypted_aes_key + encrypted_aes_iv + encrypted_data  # Prefixo '1' indica RSA + AES


def db_decrypt_byte(encrypted_data, private_pem):
    """Descriptografa bytes, detectando se é RSA ou RSA + AES"""
    if encrypted_data[0:1] == b'0':  # Somente RSA
        return db_decrypt_rsa(encrypted_data[1:], private_pem)

    if encrypted_data[0:1] != b'1':
        raise ValueError("Invalid prefix in encrypted data")

    enc_aes_key = encrypted_data[1:1 + 256]
    enc_aes_iv = encrypted_data[1 + 256:1 + 256 + 256]
    enc_data = encrypted_data[1 + 256 + 256:]

    aes_key = db_decrypt_rsa(enc_aes_key, private_pem)
    aes_iv = db_decrypt_rsa(enc_aes_iv, private_pem)

    return db_decrypt_aes(enc_data, aes_key, aes_iv)


def db_encrypt_string(string, public_pem):
    """Criptografa uma string"""
    data = string.encode()
    encrypted_data = db_encrypt_byte(data, public_pem)
    return base64.b64encode(encrypted_data).decode()


def db_decrypt_string(encrypted_string, private_pem):
    """Descriptografa uma string"""
    decrypted_data = ''
    try:
        encrypted_data = base64.b64decode(encrypted_string)
        decrypted_data = db_decrypt_byte(encrypted_data, private_pem)
    except:
        #return f"failed to decrypt string '{encrypted_string}'"
        return ""

    return decrypted_data.decode()


def db_encrypt_rsa(data, public_pem):
    """Criptografa usando RSA"""
    public_key = serialization.load_pem_public_key(public_pem.encode())
    encrypted_data = public_key.encrypt(
        data,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return encrypted_data


def db_decrypt_rsa(encrypted_data, private_pem):
    """Descriptografa usando RSA"""
    private_key = serialization.load_pem_private_key(private_pem.encode(), password=None)
    decrypted_data = private_key.decrypt(
        encrypted_data,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return decrypted_data


def db_encrypt_aes(data, key, iv):
    """Criptografa usando AES"""
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    padded_data = data + (b' ' * (16 - len(data) % 16))  # Padding para múltiplos de 16
    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
    return encrypted_data


def db_decrypt_aes(encrypted_data, key, iv):
    """Descriptografa usando AES"""
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()
    return decrypted_data.rstrip(b' ')  # Remover padding


def db_generate_passphrase():
    """Gera uma senha aleatória"""
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz@_"
    return "".join(os.urandom(1)[0] % len(chars) for _ in range(64))


# Funções auxiliares
def convert_pem_to_binary(pem):
    """Converte uma chave PEM para binário"""
    pem_lines = pem.split("\n")
    encoded = "".join(line.strip() for line in pem_lines if not line.startswith("-----"))
    return base64.b64decode(encoded)


def base64_to_bytes(b64_string):
    """Converte uma string base64 para bytes"""
    return base64.b64decode(b64_string)


def bytes_to_base64(byte_data):
    """Converte bytes para base64"""
    return base64.b64encode(byte_data).decode()


def add_new_lines(string, length=64):
    """Adiciona quebras de linha a cada 64 caracteres"""
    return "\n".join(string[i:i + length] for i in range(0, len(string), length))


def to_private_pem(private_key):
    """Converte chave privada para formato PEM"""
    key_b64 = bytes_to_base64(private_key)
    return f"-----BEGIN RSA PRIVATE KEY-----\n{add_new_lines(key_b64)}\n-----END RSA PRIVATE KEY-----"


def to_public_pem(public_key):
    """Converte chave pública para formato PEM"""
    key_b64 = bytes_to_base64(public_key)
    return f"-----BEGIN PUBLIC KEY-----\n{add_new_lines(key_b64)}\n-----END PUBLIC KEY-----"


# Testando a implementação
if __name__ == "__main__2":
    keys = db_generate_rsa_keys()
    pub_key = keys["public_key"]
    priv_key = keys["private_key"]

    mensagem = "Teste de criptografia"
    print("Mensagem original:", mensagem)

    mensagem_criptografada = db_encrypt_string(mensagem, pub_key)
    print("Mensagem criptografada:", mensagem_criptografada)

    mensagem_descriptografada = db_decrypt_string(mensagem_criptografada, priv_key)
    print("Mensagem descriptografada:", mensagem_descriptografada)


if __name__ == "__main__":
    keys = db_generate_rsa_keys()
    pub_key = keys["public_key"]
    priv_key = keys["private_key"]

    mensagem = "Teste de criptografia"
    print("Mensagem original:", mensagem)

    mensagem_criptografada = db_encrypt_string(mensagem, pub_key)
    print("Mensagem criptografada:", mensagem_criptografada)

    mensagem_descriptografada = db_decrypt_string("MEz5xKFpsbPvEdnWhzYkKe0IHGi1eqCyoYNyo+is8jZWs0PcTHdwxRE4e3eypq6ygj0XN0cMvmnJ6sChJAgbmU+tI7PD1/5lcSls/iSB/4JEa7tsD3Tf4P8U4R9Po0wZlsgiJopJvWZ8R3edtXLZqTFxwOWF5fkRKACWv+Dp7ZOz6HjJnt8oO5VGWwXLFZ1NJqQQ8FnPmLxgk+WKM0TSnxzvbJz0hwsLnbIHHU9EUSSLiGNhcXcUMkt1a7HsbksmtK1tWc/oqPqL2JpBQK3tbv//l8ks0+ptD4aoh8n+/MncyjlXWBDgdBVm8sJnMbZMRhtXU1COASXSNC/uxmSeFoo=", priv_key)
    print("Mensagem descriptografada:", mensagem_descriptografada)