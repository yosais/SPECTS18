from random import *
from bisect import *
from statistics import *

# Simulation parameters
n = 1000  # Number of packets to be simulated
lamda = 0.7
P_err = 0.99
tau = 3
Tout = 1  # Length of timeout period
B = 10  # Size of transmitter buffer

# Initialization
clock = 0.0
evList = []
count = 0  # Used for counting simulated packets and as Pkt_ID
evID = 0  # Unique ID for each event
Timeout_Event = None  # Reference to currently pending timeout event

# Insert an event into the event list
def insert(ev): 
    insort_right(evList, ev)

# Remove an event from the event list
def cancel(ev):
    evList.remove(ev)

# Initialize state variables
Q = 0
C = 0
L = 0
D = 0
T = 0

# Output variables
Num_Received_Pkts = 0  # Pkts received successfully
Arr_Time = [0] * n 
Rec_Time = [0] * n

# Event generators
def Gen_Arr_Evt(clock):
    global count, n, lamda, evID
    if count < n:
        insert( (clock + expovariate(lamda), evID, count, Handle_Arr_Evt) )
        count += 1
        evID += 1

def Gen_Loss_Evt(clock, Pkt_ID):
    global evID
    evID += 1
    insert( (clock, evID, Pkt_ID, Handle_Loss_Evt) )

def Gen_Transmit_Evt(clock, Pkt_ID):
    global evID
    evID += 1
    insert( (clock, evID, Pkt_ID, Handle_Transmit_Evt) )

def Gen_Receive_Evt(clock, Pkt_ID):
    global evID
    evID += 1
    insert( (clock, evID, Pkt_ID, Handle_Receive_Evt) )

def Gen_Drop_Evt(clock, Pkt_ID):
    global evID
    evID += 1
    insert( (clock, evID, Pkt_ID, Handle_Drop_Evt) )

def Gen_Timeout_Evt(clock, Pkt_ID):
    global Timeout_Event, evID
    evID += 1
    Timeout_Event = (clock + Tout, evID, Pkt_ID, Handle_Timeout_Evt)
    insert( Timeout_Event )

# Event handlers

def Handle_Arr_Evt(clock, Pkt_ID):
    global Q, lamda
    Q += 1
    Gen_Arr_Evt(clock + expovariate(lamda))
    if C == 0:
        Gen_Transmit_Evt(clock, Pkt_ID)
    if Q > B:
        Gen_Loss_Evt(clock, Pkt_ID)
    # Output variable
    Arr_Time[Pkt_ID] = clock

def Handle_Loss_Evt(clock, Pkt_ID):
    global Q, L
    L += 1
    Q -= 1

def Handle_Transmit_Evt(clock, Pkt_ID):
    global C, Q, T, P_err
    C = 1
    Q -= 1
    T += 1
    Gen_Timeout_Evt(clock, Pkt_ID)
    if random() <= (1 - P_err):
        Gen_Receive_Evt(clock, Pkt_ID)

def Handle_Receive_Evt(clock, Pkt_ID):
    global C, T, Q, Num_Received_Pkts
    C = 0
    T = 0
    cancel(Timeout_Event)
    if Q > 0:
        Gen_Transmit_Evt(clock, Pkt_ID + 1)  # Next packet in queue
    # Output variable
    Num_Received_Pkts += 1
    Rec_Time[Pkt_ID] = clock

def Handle_Drop_Evt(clock, Pkt_ID):
    global D, T, C, Q
    C = 0
    T = 0
    D += 1
    Q -= 1
    if Q > 0:
        Gen_Transmit_Evt(clock, Pkt_ID + 1)

def Handle_Timeout_Evt(clock, Pkt_ID):
    global T, C, Q
    C = 0
    Q += 1
    if T == tau:
        Gen_Drop_Evt(clock, Pkt_ID)
    elif T < tau:
        Gen_Transmit_Evt(clock, Pkt_ID)  # Re-transmit same packet

# Generate initial events
Gen_Arr_Evt(0.0)

# Simulation loop
while evList:
    ev = evList.pop(0)
    clock = ev[0]
    Pkt_ID = ev[2]
    ev[3](clock, Pkt_ID) # call event handler

# Statistical summary
Delay = []
for i in range(n):
    if Rec_Time[i] > 0:
        Delay.append( Rec_Time[i] - Arr_Time[i] )
print("Average delay through the system = ", round(mean(Delay), 2))
print("Percentage of received packets = ", round((Num_Received_Pkts / n) * 100, 1))