using System;
using System.Threading.Tasks;

namespace TestNamespace
{
    public class Calculator
    {
        public int simpleAdd(int a, int b)
        {
            return a + b;
        }
        
        private static void largeMethod()
        {
            int sum = 0;
            for (int i = 0; i < 10; i++)
            {
                sum += i;
                Console.WriteLine(i);
            }
            for (int j = 0; j < 5; j++)
            {
                sum *= 2;
            }
            Console.WriteLine("Sum: " + sum);
        }
        
        protected async Task<string> asyncMethod()
        {
            await Task.Delay(1000);
            return "Done";
        }
        
        internal virtual string virtualMethod()
        {
            return "Virtual";
        }
        
        public override string ToString()
        {
            return "Calculator";
        }
    }
}
