"""
Created on Tuesday 27 January 2026

@author: Théo Poujol

info:
    Telelumen wrapper
"""

import api_tng as api

def discover_luminaires():
    try :
        lum_list = api.discover()
        
        if (len(lum_list) == 0 ) : 
            print("No luminaires found")
            return None    
        
        return lum_list
    
    except :
        return None

def connect_telelumen():    
    try :
        
        lum_list = discover_luminaires()
        
        if (lum_list is not None) :
            for i in lum_list :
                print(i.address)
                print(i.get_luminaire_serial_number())
                print()
        
        # choose to connect to one
        # choose to connect to all
        # connected to specified uid (with ip related)
        
        print("Trying to connect to " + lum.address + ' / ' + i.get_luminaire_serial_number() + '\n')
        telnet = api.openLuminaire(lum.address)
        print("-> Connection established \n")
        return lum
    except :
        print("-> Connection failed \n")
        return None
    
def disconnect_telelumen(lum) :
    try :
        api.closeLuminaire(lum.address)
        print("-> Connection closed \n")
    except :
        print("Connection not closed \n")
    
def from13to24(vec):
    #[UV1, UV2, V1, V2, RB1, RB2, B1, B2, C, G1, G2, L, PC-A, A, OR, R1, R2, DR1, DR2, FR1, FR2, FR3, IR1, IR2]

    return [.0, .0, .0, .0, vec[0], vec[1], vec[2], vec[3], vec[4], vec[5], vec[6], vec[7], vec[8], vec[9] , vec[10], vec[11], vec[12], .0, .0, .0, .0, .0, .0, .0]
    
def light(lum, vec):
    result=lum.set_drive_levels(vec)        
    if (result != 0):
        print("TELELUMEN ERROR : " + str(result))
    return result

def light_off(lum):
    
    vec = [ .0, .0, .0, .0, .0, .0, .0, .0, .0, .0, .0, .0, .0, .0 , .0, .0, .0, .0, .0, .0, .0, .0, .0, .0 ]
    lum.set_drive_levels(vec)

def get_temperature(lum):
    s = lum.get_temperature()
    return float(s)

if __name__ == "__main__":
    
    discover_luminaires()
    # lum = connect_telelumen()
    
    # if (lum is not None) :
    #     print(get_temperature(lum))
    #     disconnect_telelumen(lum)
