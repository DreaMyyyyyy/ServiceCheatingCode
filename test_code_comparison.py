from plagiarism_detection import compare_code_fragments

def test_code_comparison():
    # Java код с дополнительными методами и комментариями
    code_java_1 = """
public class HelloWorld {
    // Метод для вывода приветствия
    public static void printGreeting() {
        System.out.println("Hello, World!");
    }

    public static void main(String[] args) {
        printGreeting();
    }
}
"""

    # Java код с измененным приветствием и добавленным методом
    code_java_2 = """
public class HelloWorld {
    // Метод для вывода приветствия
    public static void printGreeting() {
        System.out.println("Hi, World!");
    }

    // Метод для вывода дополнительного сообщения
    public static void printMessage() {
        System.out.println("Welcome to the world of programming!");
    }

    public static void main(String[] args) {
        printGreeting();
        printMessage();
    }
}
"""

    # C# код с дополнительным классом и комментариями
    code_csharp_1 = """
using System;

// Класс для приветствия
public class Greetings {
    // Метод для вывода приветствия
    public static void SayHello() {
        Console.WriteLine("Hello, World!");
    }
}

public class Example {
    public static void Main(string[] args) {
        Greetings.SayHello();
    }
}
"""

    # Измененное приветствие и добавленный класс с дополнительным методом
    code_csharp_2 = """
using System;

// Класс для приветствия
public class Greetings {
    // Метод для вывода приветствия
    public static void SayHello() {
        Console.WriteLine("Hi, World!");
    }

    // Метод для вывода дополнительного сообщения
    public static void PrintMessage() {
        Console.WriteLine("Welcome to the world of programming!");
    }
}

public class Example {
    public static void Main(string[] args) {
        Greetings.SayHello();
        Greetings.PrintMessage();
    }
}
"""

    similarity_java = compare_code_fragments(code_java_1, code_java_2, 'java')
    similarity_csharp = compare_code_fragments(code_csharp_1, code_csharp_2, 'csharp')

    print(f"Similarity between Java codes: {similarity_java:.2f}")
    print(f"Similarity between C# codes: {similarity_csharp:.2f}")

if __name__ == "__main__":
    test_code_comparison()





