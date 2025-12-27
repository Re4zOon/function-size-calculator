// Sample Java test file
import org.junit.Test;

public class SampleTest {
    
    @Test
    public void testMethod() {
        System.out.println("This is a test");
        assert true;
    }
    
    @Test
    public void largeTestMethod() {
        // This is a large test method
        int a = 1;
        int b = 2;
        int c = 3;
        System.out.println("test 1");
        System.out.println("test 2");
        System.out.println("test 3");
        System.out.println("test 4");
        assert a + b == c;
    }
}
