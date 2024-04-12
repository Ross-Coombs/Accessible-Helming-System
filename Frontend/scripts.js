function getBearing(id) {
    if (id == "InputDisplay") {
        //remove degree symbol
        return num = document.getElementById(id).innerHTML.slice(0, document.getElementById("InputDisplay").innerHTML.length - 1)
    } else {
        //remove label and degree symbol
        return num = document.getElementById(id).innerHTML.split(": ", 2)[1].slice(0, document.getElementById("InputDisplay").innerHTML.length - 1)
    }
}

function returnBearing(id, value) {
    //add label
    if (id == "InputDisplay") {
        label = ""
    } else if(id == "currentHeading") {
        label = "Current: "
    } else {
        label = "Target: "
    }
    //add degree symbol and update page
    document.getElementById(id).innerHTML = label.concat(value.toString().concat("°"))
}

function setInfoMessage(message) {
    if (message == "") {
        //if message is blank, hide error display
        document.getElementById("infoMessage").style.display = "none"
    } else {
        //display error
        document.getElementById("infoMessage").innerHTML = message
        document.getElementById("infoMessage").style.display = "block"
    }
}

function input(value) {
    //get current target
    let currentInput = getBearing("InputDisplay")
    //remove leading zero
    if(currentInput.slice(0,1) == "0") {
        currentInput = currentInput.slice(1)
    }
    let tempInput = currentInput.concat(value) //temp variable to make conditions more readable
    //if 360 set to 0
    if(parseInt(tempInput) == 360) {
        tempInput = 0
        setInfoMessage("360° is the same as 0°")
    }
    //check input is a valid bearing
    if((parseInt(tempInput) < 360) && (parseInt(tempInput) >= 0)) {
        currentInput = tempInput
    //if not a valid bearing, remove first character and check its valid
    } else if((parseInt(tempInput.slice(1)) < 360) && (parseInt(tempInput.slice(1)) >= 0)) {
        currentInput = tempInput.slice(1)
        setInfoMessage("A bearing must be between 0-360°")
    } else {
        setInfoMessage("A bearing must be between 0-360°")
    }
    //update display
    returnBearing("InputDisplay", currentInput)
}

function adjust(operator) {
    //get current target
    let currentInput = getBearing("InputDisplay")
    //plus or minus 5 depending on input
    if(operator == "+") {
        currentInput = parseInt(currentInput)+5
        //loop 360 to 0
        if(currentInput > 359) {
            currentInput = currentInput - 360
            setInfoMessage("360° loops back to 0°")
        }
    } else if(operator == "-") {
        currentInput = parseInt(currentInput)-5
        //loop 0 to 360
        if(currentInput < 0) {
            currentInput = currentInput + 360
            setInfoMessage("0° loops back to 360°")
        }
    } else {
        console.log("Invalid operator in adjust function")
    }
    //update display
    returnBearing("InputDisplay", currentInput)
}

function empty() {
    //reset input field
    returnBearing("InputDisplay", 0)
    setInfoMessage("")
}

function enter() {
    //send to backend
    socket.send("Target:".concat(getBearing("InputDisplay")))
    //display new target on label and compass
    returnBearing("targetHeading", getBearing("InputDisplay"))
    document.getElementById("targetPointer").style.display = "grid"
    document.getElementById("targetPointer").style.transform = "rotate(".concat(getBearing("InputDisplay")).concat("deg)")
    setInfoMessage("")
}

function setupCompass() {
    var compassPoints = document.getElementsByClassName('compassPoint'); //get all compass points
    for(var index=0;index < compassPoints.length;index++){ //loop through all compass points
        compassPoints[index].style.transform = 'rotate('.concat(45 * compassPoints[index].id).concat('deg)') //spread compass points equally around the circle
        compassPoints[index].childNodes[0].style.transform = 'rotate('.concat((-45 * compassPoints[index].id)).concat('deg)') //unrotate the text to maintain readability
    }
}

//connect to websocket at same address as current window
const socket = new WebSocket('ws://'.concat(window.location.href.split(":", 2)[0]).concat('.201.89.210:8000');
socket.addEventListener('open', function (event) {
    socket.send('Connection Established')
});

//listen for websocket error
socket.addEventListener('error', function (event) {
    console.error('WebSocket error observed:', event);
    setInfoMessage("Error connecting to boat")
});

socket.addEventListener('message', function (event) {
    //log recieved input
    console.log("Received: ".concat(event.data))
    //if recieving heading, update page
    if (event.data.includes("Heading")) {
        let currentHeading = parseInt(event.data.split(":", 2)[1], 10); 
        returnBearing("currentHeading", currentHeading) //display heading
        //turn compass to reflect current heading
        document.getElementById("compass").style.transform = 'rotate('.concat(-currentHeading).concat('deg)') //turn whole compass
        var compassPoints = document.getElementsByClassName('compassPoint'); //get all compass points
        for(var index=0;index < compassPoints.length;index++){ //loop through all compass points
            compassPoints[index].style.transform = 'rotate('.concat(45 * compassPoints[index].id).concat('deg)') //spread compass points equally around the circle
            compassPoints[index].childNodes[0].style.transform = 'rotate('.concat(((-45 * compassPoints[index].id) + currentHeading)).concat('deg)') //unrotate the text to maintain readability
        }
        //remove target indicator if facing correct way
        if (currentHeading == getBearing("targetHeading")) {
            document.getElementById("targetPointer").style.display = "none"
        }
    }
});
