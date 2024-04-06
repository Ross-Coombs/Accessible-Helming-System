import asyncio
import websockets
from gpiozero import AngularServo
from time import sleep
from websockets.exceptions import ConnectionClosed

servo = AngularServo(18, min_angle=-90, max_angle=90, min_pulse_width=0.00075, max_pulse_width=0.0025)
targetBearing = 0
currentBearing = 0
rudderAngle = 0
active_websocket = None

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

async def start_server():
    await websockets.serve(receive, "0.0.0.0", 8000)

def setAngle(angle):
	global rudderAngle
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
	try:
		rudderAngle = angle
		servo.angle = angle
	except:
		print("Error turning servo")

def closestToZero(array):
	min = 900
	for i in array:
		if abs(i) < abs(min):
			min = i
	return min

async def main():
	global currentBearing, active_websocket
	while True:	
		#if rudder is angled simulate turning the boat, turn boat faster the greater the rudder angle
		if rudderAngle > 0:
			currentBearing += int(rudderAngle/10)
			if currentBearing > 359:
				currentBearing = currentBearing - 360
		elif rudderAngle < 0:
			currentBearing -= -int(rudderAngle/10)
			if currentBearing < 0:
				currentBearing = currentBearing + 360
		#send current bearing to client
		# Check if there is an active websocket connection
		if active_websocket:
			# Send current bearing to client
			await active_websocket.send(str("Heading:{}".format(currentBearing)))

		#a b c represent how many degrees apart the target and current bearings are, in different directions
		#if the cloest of these 3 values to zero (shorestDist variable) is negative, the shortest direction is left, if its postivive, right, zero, no change needed
		possibleRoutes= [(targetBearing - currentBearing), (targetBearing - currentBearing + 360), (targetBearing - currentBearing - 360)]
		shorestDist = closestToZero(possibleRoutes)
		#if pointing in correct direction, keep the rudder straight
		if currentBearing == targetBearing:
			setAngle(0)
		#if quicker to turn right, turn right
		elif shorestDist > 0:
			setAngle(max(shorestDist/2, 10)) #rudder angle is greater, the bigger the turn, with a minimum of 10 degrees
		#if not, turn left
		else:
			setAngle(min(shorestDist/2, -10))
		await asyncio.sleep(0.5)

		print("Current Bearing: {} | Target Bearing: {} | Rudder Angle: {}".format(currentBearing, targetBearing, rudderAngle))


# Run both the websocket server and the main function concurrently
# Start the event loop and create tasks for both coroutines
async def run_both():
    # Create a task for the server coroutine
    server_task = asyncio.create_task(start_server())
    print("Server coroutine has been started.")
    
    # Run the main function alongside the server
    await asyncio.gather(
        server_task,
        main()
    )

# Start the event loop
asyncio.run(run_both())