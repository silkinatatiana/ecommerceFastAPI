class NotMoreProductsException(Exception):
    def __str__(self):
        return "Товар закончился на складе"

