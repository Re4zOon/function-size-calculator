# Sample Python file for testing

def simple_function():
    """A simple function."""
    print("Hello, World!")


def large_function(x, y):
    """A larger function with multiple statements."""
    result = 0
    for i in range(x):
        if i % 2 == 0:
            result += i
        else:
            result -= i
    
    for j in range(y):
        result *= 2
    
    return result


class MyClass:
    """Sample class with methods."""
    
    def __init__(self):
        """Initialize the class."""
        self.value = 0
    
    def instance_method(self):
        """An instance method."""
        self.value += 1
        return self.value
    
    @staticmethod
    def static_method():
        """A static method."""
        return "static"
    
    @classmethod
    def class_method(cls):
        """A class method."""
        return cls


async def async_function():
    """An async function."""
    import asyncio
    await asyncio.sleep(1)
    return "done"


def function_with_nested():
    """A function with a nested function."""
    x = 10
    
    def nested():
        """Nested function."""
        return x * 2
    
    return nested()
