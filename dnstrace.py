#!/usr/bin/env python3
import requests, time ,os, subprocess, math, sys, threading, socket
from os import system
loading_done = [False]
global announce
announce = "\033[95mdnstrace\033[0m:"
global host_address
host_address = requests.get("https://ipv4.icanhazip.com/")
host_address = host_address.text.strip()

def loading_anim():
    loading_symbols = ["⣾","⣽","⣻","⢿","⡿","⣟","⣯","⣷"]
    idx = 0
    while not loading_done[0]:
        sys.stdout.write(f"\rRequesting from \033[95m{target_ip}\033[0m {loading_symbols[idx]}")
        sys.stdout.flush()
        idx = (idx + 1) % len(loading_symbols)
        time.sleep(0.1)  # Adjust speed of the loading animation

def validate_address(ip_address):
    response = os.system(f"ping -c 1 {ip_address} > /dev/null 2>&1")
    if response == 0:
        return True
    else:
        return False


def get_inf(ip_address):
    response = requests.get(f"http://ip-api.com/json/{ip_address}?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,asname,reverse,mobile,proxy,hosting,query")
    return response.json()

def get_dns(ip_address):
    try:
        dns_name = socket.gethostbyaddr(ip_address)[0]
        return dns_name
    except socket.herror:
        return "No DNS Found"

def print_info(json_format):
    if target_ip[0].isdigit():
        dns_name = get_dns(target_ip)
    else:
        dns_name = json_format['query']
    dns_string = f" {target_ip} | {dns_name}"
    dns_uline = (len(dns_string) * "-")
    print(f"""
        \033[95m{target_ip} \033[90m| \033[95m{dns_name}
        \033[90m{dns_uline}


          \033[0m""")
def get_score(ip_address, host_address, packets):
    if not host_address:
        try:
            host_address = requests.get("https://ipv4.icanhazip.com/")
            host_address = host_address.text.strip()
        except requests.RequestException as e:
            print(f"Error fetching host address: {e}")
            return None
    if not packets:
        packets = 1
    start = time.time()
    if packets > 5:
        response = subprocess.run(['ping', '-c', "3", ip_address], capture_output=True, text=True)
        output = response.stdout
        lines = output.splitlines()
        avg_latency_line = [line for line in lines if 'avg' in line]
        if avg_latency_line:
            approx_time = float(avg_latency_line[0].split('/')[-3])
            approx_time = approx_time / 3
            #print(approx_time)
        else:
            approx_time = 0  
        #print(f"\033[90mDue To Large Packet Size, Estimated Time: ~{math.ceil(((approx_time)))} Seconds\033[0m")
    end = time.time()
    #print(end - start)
    start = time.time()
    response = subprocess.run(['ping', '-c', str(packets), ip_address], capture_output=True, text=True)
    if response.returncode == 0:
        output = response.stdout
        lines = output.splitlines()

        packet_loss_line = [line for line in lines if 'packet loss' in line]
        if packet_loss_line:
            packet_loss = int(packet_loss_line[0].split('%')[0].split()[-1])
        else:
            packet_loss = None 

        avg_latency_line = [line for line in lines if 'avg' in line]
        if avg_latency_line:
            avg_latency = float(avg_latency_line[0].split('/')[-3])
        else:
            avg_latency = None  
        end = time.time()
        #print(end - start)
        return {
            'packet_loss': packet_loss,
            'avg_latency': avg_latency,
        }
    else:
        print("Ping failed.")
        return None


def get_strenght(score_dict):
    score = 100
    score -= score_dict['packet_loss'] * 2
    score -= (score_dict['avg_latency'] * 2)
    def get_visual(score):
        visual = ""
        out_of = 10
        scalable_score = int(score / 10)
        remainder = abs(scalable_score - out_of)
        if scalable_score >= 8:
            bar_col = "\033[92m"
        elif scalable_score >= 5:
            bar_col = "\033[93m"
        else:
            bar_col = "\033[91m"
        if scalable_score:
            visual += bar_col
            visual += scalable_score * "██"
            visual += '\033[90m'
            visual += remainder * "██"
            visual += "\033[0m"
        return visual
    visual = get_visual(score)
    print(visual, int(score), "%")
    return max(score, 0)

def scrape_args(list_args):
    arg_map = {
            "paksize": 1,
            "sendfrom": host_address,
            "addfile": None,
            "type": "json",
            }

    # take care of the packet size arguement
    if "ps" in list_args:
        paksize_arg = list_args.index("ps")
        if paksize_arg+1 >= len(list_args):
            print(announce,"Arguement defined, but no packetsize was provided")
            exit(1)
        paketsize = list_args[paksize_arg+1]
        if not paketsize.isdigit():
            print(announce,"Packet size provided was not an int")
            exit(1)
        arg_map['paksize'] = int(paketsize)
        list_args.pop(paksize_arg)
        list_args.pop(list_args.index(paketsize))
    # take care of send from arguement
    if "sf" in list_args:
        sendfrom_arg = list_args.index("sf")
        if sendfrom_arg+1 >= len(list_args):
            print(announce, "Arguement was defined, but no IP/DNS was provided")
            exit(1)
        sendfromloc = list_args[sendfrom_arg+1]
        ipresponse = subprocess.run(['ping', '-c', '1', sendfromloc], capture_output=True, text=True)
        if ipresponse.returncode != 0:
            print(announce,"Provided IP/DNS is not active, or does not exist")
            exit(1)
        arg_map['sendfrom'] = sendfromloc
        list_args.pop(sendfrom_arg)
        list_args.pop(list_args.index(sendfromloc))
    # take care of put arg
    if "put" in list_args:
        put_arg = list_args.index("put")
        if put_arg+1 >= len(list_args):
            print(announce,"Arguement was defined, but no FILE PATH was provided")
            exit(1)
        putfile = list_args[put_arg+1]
        arg_map['addfile'] = putfile
        list_args.pop(put_arg)
        list_args.pop(list_args.index(putfile))
    # take care of format
    options = ['json','xml','csv','newline']
    arg_map['type'] = 'json'
    for option in options:
        if option in list_args:
            arg_map['type'] = option
            list_args.pop(list_args.index(option))

    # now we clean up the args
    if list_args[2:]:
        left_overs = ", ".join(list_args[2:])
        print(announce,f"Unrecognized Args '\033[90m{left_overs}'\033[0m")
    return arg_map

def connected():
    if host_address:
        return True
    return False


def main():
    """
    the first arg is reserved for a dns/ipv4/ipv6 (if given the string of "home", will provide device ip)
    the values will only be detected after every arg, if they require values
    ps, -packetsize (packet size) -> optional arg (if not given, will default to 0)
        reserves x+1 for the packet variable
    sf, -sendfrom (send from) -> optional ip (if not given will send from home ip), gets info from a designated server
        reserves x+1 for the ip
    put -> optional ip (if not given, will do nothing)
        reserves x+1 for the putfile
    (type) -> optional choices (json,xml,csv,newline) (if not given, will default to json)

    -
    """

    if not connected():
        print(announce, "not connected to a stable network")
        exit(1)
    if len(sys.argv) < 2:
        print(announce, "IP arguement has not been provided")
        exit(1)
    global target_ip
    target_ip = sys.argv[1]
    if not validate_address(target_ip):
        print(announce, "an invalid IP address was provided")
        exit(1)
    arg_map = scrape_args(sys.argv)
  
    loading_done[0] = False
    loading_thread = threading.Thread(target=loading_anim)
    loading_thread.start()
    # this is where the working should happen
    ip_information = get_inf(target_ip)
    dictio = get_score(target_ip,arg_map['sendfrom'],arg_map['paksize'])
    loading_done[0] = True
    loading_thread.join()
    sys.stdout.write("\r" + " " * 50 + "\r")
    sys.stdout.flush()
    # now this is where the outputs should take place
    print_info(ip_information)
    print(ip_information)
    get_strenght(dictio)

if __name__ == "__main__":
    main()
