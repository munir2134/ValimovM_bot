import hashlib
import base64

def generate_key(key: str, length: int) -> bytes:
    hash_key = hashlib.sha256(key.encode()).digest()
    return (hash_key * (length // len(hash_key) + 1))[:length]

def permute(data: bytes, key: str) -> bytes:
    indexes = list(range(len(data)))
    seed = sum(ord(c) for c in key)
    for i in range(len(indexes)):
        j = (i + seed) % len(indexes)
        indexes[i], indexes[j] = indexes[j], indexes[i]
    return bytes(data[i] for i in indexes)

def inverse_permute(data: bytes, key: str) -> bytes:
    indexes = list(range(len(data)))
    seed = sum(ord(c) for c in key)
    for i in range(len(indexes)):
        j = (i + seed) % len(indexes)
        indexes[i], indexes[j] = indexes[j], indexes[i]

    original = [0] * len(data)
    for i, idx in enumerate(indexes):
        original[idx] = data[i]
    return bytes(original)

def encrypt(text: str, key: str) -> str:
    data = text.encode("utf-8")
    k = generate_key(key, len(data))
    xored = bytes(b ^ k[i] for i, b in enumerate(data))
    permuted = permute(xored, key)
    return base64.b64encode(permuted).decode()

def decrypt(cipher: str, key: str) -> str:
    data = base64.b64decode(cipher)
    unpermuted = inverse_permute(data, key)
    k = generate_key(key, len(unpermuted))
    original = bytes(b ^ k[i] for i, b in enumerate(unpermuted))
    return original.decode("utf-8")

# ===== Тест =====
if __name__ == "__main__":
    text = input("Введите текст: ")
    key = input("Введите ключ: ")

    encrypted = encrypt(text, key)
    print("Зашифрованный текст:\n", encrypted)

    decrypted = decrypt(encrypted, key)
    print("Расшифрованный текст:\n", decrypted)
