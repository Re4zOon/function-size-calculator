// Sample JavaScript file for testing

function simpleFunction() {
    console.log("Hello");
}

function largeFunction() {
    let x = 1;
    let y = 2;
    let z = 3;
    if (x > 0) {
        console.log("x is positive");
    }
    return x + y + z;
}

const arrowFunction = () => {
    return "arrow";
}

const asyncArrowFunction = async () => {
    await Promise.resolve();
    return "async arrow";
}

class MyClass {
    methodInClass() {
        console.log("method");
    }
    
    async asyncMethod() {
        await Promise.resolve();
        console.log("async method");
    }
}

// Nested function test
function outerFunction() {
    console.log("outer");
    function innerFunction() {
        console.log("inner");
    }
    innerFunction();
}
