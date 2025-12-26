// Sample TypeScript file for testing

function typedFunction(name: string): string {
    return `Hello, ${name}`;
}

const typedArrow = (x: number): number => {
    return x * 2;
}

interface MyInterface {
    name: string;
}

class TypedClass {
    public publicMethod(): void {
        console.log("public");
    }
    
    private privateMethod(): void {
        console.log("private");
    }
    
    protected protectedMethod(): void {
        console.log("protected");
    }
}
