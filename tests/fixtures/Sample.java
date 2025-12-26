// Sample Java file for testing

public class Sample {
    
    public void publicMethod() {
        System.out.println("public method");
    }
    
    private void privateMethod() {
        System.out.println("private method");
    }
    
    protected static void protectedStaticMethod() {
        System.out.println("protected static");
    }
    
    public static final void publicStaticFinalMethod() {
        System.out.println("public static final");
    }
    
    public synchronized int synchronizedMethod() {
        return 42;
    }
    
    public void methodWithException() throws Exception {
        throw new Exception("test");
    }
    
    public String largeMethod(int x, String y) {
        int a = 1;
        int b = 2;
        int c = 3;
        if (x > 0) {
            System.out.println("positive");
        } else {
            System.out.println("negative");
        }
        return y + a + b + c;
    }
    
    // Method with generic return type
    public <T> List<T> genericMethod() {
        return new ArrayList<>();
    }
}
