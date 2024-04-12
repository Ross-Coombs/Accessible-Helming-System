#import libraries
import asyncio
import websockets
import pi_servo_hat
from time import sleep
from websockets.exceptions import ConnectionClosed

#setup global variables
servo = pi_servo_hat.PiServoHat()
targetBearing = 0
active_websocket = None

def setRudderAngle(angle):
	#ensure input is an int
	try:
		angle = int(angle)
	except:
		angle = 0
		
	#ensure angle is within acceptable range
	if(angle > 90):
		angle = 90
	elif(angle < -90):
		angle = -90
		
	#set angle
	rudderActuator(angle)
	return angle

#this function can be changed to fit output, for example a yacht autopilot tall ship rudder motor, or model boat servo.
def rudderActuator(angle):
	#add 90 degrees to angle as servos range is 0 - 180
	servo.move_servo_position(0, adjust_angle_for_library(angle+90), 180)
	servo.move_servo_position(1, adjust_angle_for_library(angle+90), 180)

#Library does not use correct servo pulse width and does not allow changing it. This function adjusts the angle to compensate.
def adjust_angle_for_library(actual_angle):
    # Calculate the correct pulse width for the actual angle
    desired_pulse_width = 0.75 + (actual_angle * (1.75 / 180))
    # Calculate the equivalent angle for librarys expected range
    library_angle = (desired_pulse_width - 1) * 180 / 1.0
    return library_angle

#gets the current bearing the boat is facing
def getCurrentHeading(currentHeading, rudderAngle):
	#as this version is not attached to a real boat this function also simulates the boat turning, and as such requires rudderAngle and currentHeading
	#if rudder is angled simulate turning the boat, turn boat faster the greater the rudder angle
		if rudderAngle > 0:
			currentHeading += int(rudderAngle/10)
			if currentHeading > 359:
				currentHeading = currentHeading - 360
		elif rudderAngle < 0:
			currentHeading -= -int(rudderAngle/10)
			if currentHeading < 0:
				currentHeading = currentHeading + 360
		return currentHeading

#calculate the value closest to zero in an array
def closestToZero(array):
	min = 900
	for i in array:
		if abs(i) < abs(min):
			min = i
	return min

async def main():
	#setup variables
	global active_websocket
	rudderAngle = 0
	currentHeading = 0
	servo.restart() #restart servo
	while True:	
		#get current direction from the boat
		currentHeading = getCurrentHeading(currentHeading, rudderAngle)		
		#each value in the array represents how many degrees apart the target and current bearings are, in different directions
		#if the closest of these 3 values to zero (shortestDist variable) is negative, the shortest direction is left, if its postivive, right, zero, no change needed
		possibleRoutes= [(targetBearing - currentHeading), (targetBearing - currentHeading + 360), (targetBearing - currentHeading - 360)]
		shortestDist = closestToZero(possibleRoutes)
		#if pointing in correct direction, keep the rudder straight
		if currentHeading == targetBearing:
			rudderAngle = setRudderAngle(0)
		#if quicker to turn right, turn right
		elif shortestDist > 0:
			rudderAngle = setRudderAngle(max(shortestDist, 10)) #rudder angle is greater, the bigger the turn, with a minimum of 10 degrees
		#if not, turn left
		else:
			rudderAngle = setRudderAngle(min(shortestDist, -10))
		#Telemetry
		# Check if there is an active websocket connection
		if active_websocket:
			# Send current bearing to client
			await active_websocket.send(str("Heading:{}".format(currentHeading)))
		#display all telemetry
		print("Current Bearing: {} | Target Bearing: {} | Rudder Angle: {}".format(currentHeading, targetBearing, rudderAngle))
		await asyncio.sleep(0.25) #refresh rate

#setup websocket
async def receive(websocket, path):
	global active_websocket
	active_websocket = websocket
	global targetBearing
	try:
		async for message in websocket:
			print(f"Received: {message}")
			if "Target" in message:
				targetBearing = int(message.split(":", 1)[1])
				print("Set target to: " + str(targetBearing))
			await websocket.send(message)  #Sending back the received message
	except ConnectionClosed:
		print("WebSocket connection closed")
	finally:
		#Reset the global variable on disconnection
		active_websocket = None

#function to start the websocket
async def startWebSocket():
    await websockets.serve(receive, "0.0.0.0", 8000)

# Run both the websocket server and the main function concurrently
# Start the event loop and create tasks for both coroutines
async def run_both():
    # Create a task for the server coroutine
    server_task = asyncio.create_task(startWebSocket())
    # Run the main function alongside the server
    await asyncio.gather(
        server_task,
        main()
    )

# Start the event loop
asyncio.run(run_both())