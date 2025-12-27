// Sample JavaScript test file

function testFunction() {
    console.log("This is a test function");
    expect(true).toBe(true);
}

const largeTestFunction = () => {
    // Large test function
    const a = 1;
    const b = 2;
    const c = 3;
    console.log("test 1");
    console.log("test 2");
    console.log("test 3");
    console.log("test 4");
    expect(a + b).toBe(c);
};
