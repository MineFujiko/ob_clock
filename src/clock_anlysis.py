import argparse
import datetime

def get_item_info(line):
    return line.split(" ")[-1].strip()


def extract_info(file_path):
    with open(file_path, 'r', encoding='utf-8') as f: 
        file_info = f.readlines()
    f.close()

    # LOG_CLOCK: 2024-08-17 22:00 -- 2024-08-17 22:38 => 38

    # item_lsit: list
    # item: dic
    # - item_info: str, title
    # - LOG_CLOCK: list
    #   - start_time: str
    #   - end_time  : str
    #   - utime     : int (min)
    # - LOG_TYPE : str
    # - LOG_EFF  : int

    item_list = []
    hit_flag = 0
    for line_num, line in enumerate(file_info):
        if "LOG_CLOCK:" in line:
            curr_line_num = line_num
            hit_flag = 1 if hit_flag == 0 else 0
            start_time = line.split("LOG_CLOCK:")[1].split("--")[0].strip()
            end_time   = line.split("LOG_CLOCK:")[1].split("--")[1].split("=>")[0].strip()
            utime      = line.split("LOG_CLOCK:")[1].split("--")[1].split("=>")[1].strip()

            log_clock = {}
            log_clock["start_time"] = start_time
            log_clock["end_time"]   = end_time
            log_clock["utime"] = utime # TODO check

            if hit_flag:
                new_item = {}
                item_info = get_item_info(file_info[curr_line_num-1])
                new_item["item_info"] = item_info
                new_item["LOG_CLOCK"] = [log_clock]
                item_list.append(new_item)
            else:
                item_list[-1]["LOG_CLOCK"].append(log_clock)
        else:
            hit_flag = 0
        
        if "LOG_TYPE" in line:
            log_type = line.split(":")[1].strip()
            item_list[-1]["LOG_TYPE"]  = log_type

        if "LOG_EFF" in line:
            log_eff = line.split(":")[1].strip()
            item_list[-1]["LOG_EFF"] = log_eff
        

    return item_list

def time_range_filter(item_list, cfg_time_range):
    # min unit is day
    start_day = cfg_time_range[0]
    end_day = cfg_time_range[1]
    start_day_obj = datetime.datetime.strptime(start_day, "%Y-%m-%d")
    end_day_obj = datetime.datetime.strptime(end_day, "%Y-%m-%d")

    item_list_fliter = []
    for i, item in enumerate(item_list):
        item_day = item["LOG_CLOCK"][0]["start_time"].split(" ")[0]
        item_day_obj = datetime.datetime.strptime(item_day, "%Y-%m-%d")
        if (item_day_obj >= start_day_obj) and (item_day_obj <= end_day_obj):
            item_list_fliter.append(item)
    
    return item_list_fliter

def get_all_type(item_list):
    all_type = []
    for item in item_list:
        log_type = item["LOG_TYPE"] 
        all_type.append(log_type)
    # remove the same type
    all_type = set(all_type)
    all_type = list(all_type)
    # [[type,idx]]
    type_info = []
    for i,type in enumerate(all_type):
        type_info.append([type,i])
    return type_info

def calc_utime(start_time, end_time):
    # start_time = start_time.split(" ")[1]
    # end_time   = end_time.split(" ")[1]
    # TODO all save time by datetime
    start_time_obj = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M")
    end_time_obj = datetime.datetime.strptime(end_time, "%Y-%m-%d %H:%M")
    utime  = (end_time_obj - start_time_obj).min
    return utime

def item_time_calc(item_list):
    # item_lsit: list
    # item: dic
    # - item_info: str, title
    # - LOG_CLOCK: list
    #   - start_time: str
    #   - end_time  : str
    #   - utime     : int (min)
    # - LOG_TYPE : str
    # - LOG_EFF  : int
    # - total_time: int(min)
    new_item_list = []
    for item in item_list:
        log_clock_list = item["LOG_CLOCK"]
        total_time = 0
        for log_item in log_clock_list:
            utime = int(log_item["utime"])
            if utime == "":
                start_time = log_item["start_time"]
                end_time   = log_item["end_time"]
                utime = calc_utime(start_time, end_time)
            total_time += utime
        item["total_time"] = total_time
        new_item_list.append(item)
    return new_item_list

def get_item_index(all_type, item_type):
    index = 0
    for item in all_type:
        __type = item[0]
        if __type == item_type:
            index = item[1]
            break
    return index

def parse_by_type(item_list, all_type):
    for item in item_list:
        item_type = item["LOG_TYPE"]
        item_index = get_item_index(all_type, item_type)
        # put into all_type
        if len(all_type[item_index]) == 2:
            all_type[item_index].append([item])
        else:
            all_type[item_index][2].append(item)
    return all_type

def parse_info(item_list, cfg_time_range):
    # item time calc
    item_list = item_time_calc(item_list)
    # time range filter
    item_list = time_range_filter(item_list, cfg_time_range)
    # type parse
    all_type = get_all_type(item_list)
    #  
    item_list_by_type = parse_by_type(item_list, all_type)
    return item_list_by_type

def get_total_time(item_info):
    total_time = 0
    for item in item_info:
        __time = item["total_time"] 
        total_time += __time
    return total_time

def output_info(item_list):
    # output info by type
    # type total_time
    time_by_type = [] # [type, total_time]
    for item in item_list:
        item_type = item[0]
        item_info = item[2]
        total_time = get_total_time(item_info)
        time_by_type.append([item_type,total_time])
    
    # sorted
    time_by_type = sorted(time_by_type, key=lambda x:x[1], reverse=True)
    
    # print to log file
    with open("clock_analysis.log", "w", encoding='utf-8') as f:
        f.write("type total_time\n")
        for item in time_by_type:
            f.write("{0} {1}\n".format(item[0], item[1]))
    f.close()


def clock_analysis(file_path):

    parser = argparse.ArgumentParser()
    parser.add_argument("-st", "--start_time", type=str, help="start time, 2024-08-18")
    parser.add_argument("-et", "--end_time", type=str, help="end time, 2024-08-18")
    parser.add_argument("--this_dat", "-td", type=str, help="this day")
    parser.add_argument("--last_dat", "-ld", type=str, help="last day")
    parser.add_argument("--this_week", "-tw", type=str, help="this week")
    parser.add_argument("--last_week", "-lw", type=str, help="last week")
    parser.add_argument("--this_month", "-tm", type=str, help="this month")
    parser.add_argument("--last_month", "-lm", type=str, help="last month")
    parser.add_argument("--all", "-a", type=str, help="all")

    parser.add_argument("--path", "-p", type=str, help="path")

    parser.add_argument("--type", "-t", type=str, help="type")
    parser.add_argument("--graph", "-g", type=str, help="graph")
    parser.add_argument("--sort", "-s", type=str, help="sort by time/type")

    args = parser.parse_args()

    # time cfg
    if args.start_time:
        cfg_start_time = args.start_time
    else:
        # cfg_start_time = ""
        cfg_start_time = "2024-08-16"

    if args.end_time:
        cfg_end_time = args.end_time
    else:
        # cfg_end_time = ""
        cfg_end_time = "2024-08-18"

    
    cfg_time_range = [cfg_start_time,cfg_end_time]


    item_list = extract_info(file_path)
    item_list = parse_info(item_list, cfg_time_range)
    output_info(item_list)


if __name__ == '__main__':
    file_path = r"test.md"

    clock_analysis(file_path)