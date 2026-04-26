import math


job_name = "Example 1"

radius = 103.776
tangent_length = 328.0832
lane_width = 3.5
number_of_lanes = 8

finish_offset = 0.0

curb_present = False
hurdles_300_present = True
hurdles_400_present = True
steeplechase_present = False

distance_pt_to_wj = 185.433
distance_wj_to_pt = 184.843
wj_between_pt1_pt2 = True
wj_between_pt3_pt4 = False


def round4(value):
    return round(value + 0.0000000001, 4)


def off(value):
    return round4(value - finish_offset)


def measurement_offset(curb_present):
    return 0.984 if curb_present else 0.6562


def format_dms(decimal_degrees):
    negative = decimal_degrees < 0
    decimal_degrees = abs(decimal_degrees)

    degrees = int(decimal_degrees)
    minutes_float = (decimal_degrees - degrees) * 60
    minutes = int(minutes_float)
    seconds = round((minutes_float - minutes) * 60)

    if seconds == 60:
        seconds = 0
        minutes += 1

    if minutes == 60:
        minutes = 0
        degrees += 1

    sign = "-" if negative else ""
    return f'{sign}{degrees:02d}°{minutes:02d}\'{seconds:02d}"'


def mark_display(value, lane, front_straight="from_pt2", home_straight="from_pt4"):
    display_distance = off(value)

    arc = lane["arc_raw"]
    lap = lane["total_lane_length"]
    deg_per_ft = lane["degrees_per_foot"]

    pos = value % lap

    pt1 = 0
    pt2 = arc
    pt3 = arc + tangent_length
    pt4 = (2 * arc) + tangent_length

    if pt1 <= pos <= pt2:
        return f"{display_distance} {format_dms(pos * deg_per_ft)}"

    if pt2 < pos < pt3:
        if front_straight == "to_pt3":
            return f"{display_distance} {round4(pos - pt3)}"
        if front_straight == "nearest":
            from_pt2 = pos - pt2
            to_pt3 = pos - pt3
            return f"{display_distance} {round4(from_pt2 if abs(from_pt2) <= abs(to_pt3) else to_pt3)}"
        return f"{display_distance} {round4(pos - pt2)}"

    if pt3 <= pos <= pt4:
        return f"{display_distance} {format_dms((pos - pt3) * deg_per_ft)}"

    if home_straight == "to_pt1":
        return f"{display_distance} {round4(pos - lap)}"
    if home_straight == "nearest":
        from_pt4 = pos - pt4
        to_pt1 = pos - lap
        return f"{display_distance} {round4(from_pt4 if abs(from_pt4) <= abs(to_pt1) else to_pt1)}"
    return f"{display_distance} {round4(pos - pt4)}"


def mark_with_angle(value, lane):
    return mark_display(value, lane)


def mark_to_pt3(value, lane):
    return mark_display(value, lane, front_straight="to_pt3")


def mark_to_pt1(value, lane):
    return mark_display(value, lane, home_straight="to_pt1")


def mark_nearest_pc(value, lane):
    return mark_display(value, lane, front_straight="nearest", home_straight="nearest")

def format_mark(mark):
    pt, value = mark
    return f"{pt} {value}"


def calculate_lanes(radius, tangent_length, lane_width, number_of_lanes, curb_present=False):
    base_measurement_radius = radius + measurement_offset(curb_present)
    lanes = []

    for lane in range(1, number_of_lanes + 1):
        path_radius = base_measurement_radius + ((lane - 1) * lane_width)
        arc_raw = math.pi * path_radius
        length_one_degree = arc_raw / 180
        degrees_per_foot = 1 / length_one_degree
        total_lane_length = (2 * tangent_length) + (2 * arc_raw)

        lanes.append({
            "lane": lane,
            "path_measurement": round4(path_radius),
            "arc_raw": arc_raw,
            "length_of_arc": round4(arc_raw),
            "length_one_degree": round(length_one_degree, 6),
            "degrees_per_foot": round(degrees_per_foot, 6),
            "total_lane_length": round4(total_lane_length),
        })

    return lanes


def lane_stagger(lane, lane1_total):
    return lane["total_lane_length"] - lane1_total


def crossover_length(lane_number, lane_width, tangent_length):
    lateral_offset = (lane_number - 1) * lane_width
    return math.sqrt((tangent_length ** 2) + (lateral_offset ** 2)) - tangent_length


def stagger_turn3(lane, lane1_total, lane_width, tangent_length):
    stagger = lane_stagger(lane, lane1_total)
    cross = crossover_length(lane["lane"], lane_width, tangent_length)
    return (stagger * 1.5) + cross


def calculate_point_to_point(lanes, tangent_length):
    results = []

    for lane in lanes:
        arc = lane["arc_raw"]

        results.append({
            "lane": lane["lane"],
            "pc1_to_pc2": round4(arc),
            "pc1_to_pc3": round4(arc + tangent_length),
            "pc1_to_pc4": round4((2 * arc) + tangent_length),
            "pc1_to_pc1": round4((2 * arc) + (2 * tangent_length)),
        })

    return results


def calculate_distance_greater_than_lane_one(lanes):
    results = []
    lane1_total = lanes[0]["total_lane_length"]

    for lane in lanes:
        stagger = lane_stagger(lane, lane1_total)

        results.append({
            "lane": lane["lane"],
            "turn1": round4(stagger / 2),
            "turn2": round4(stagger),
            "turn3": round4(stagger * 1.5),
            "turn4": round4(stagger * 2),
        })

    return results


def calculate_crossover_lengths(lanes, lane_width, tangent_length):
    results = []
    lane1_total = lanes[0]["total_lane_length"]

    for lane in lanes:
        stagger = lane_stagger(lane, lane1_total)
        cross = crossover_length(lane["lane"], lane_width, tangent_length)

        turn1 = (stagger / 2) + cross
        turn3 = (stagger * 1.5) + cross

        results.append({
            "lane": lane["lane"],
            "distance": round4(cross),
            "turn1_angle": format_dms(turn1 * lane["degrees_per_foot"]),
            "turn3_angle": format_dms(turn3 * lane["degrees_per_foot"]),
        })

    return results


def calculate_stagger_starts(lanes, lane_width, tangent_length):
    results = []
    lane1_total = lanes[0]["total_lane_length"]

    for lane in lanes:
        stagger = lane_stagger(lane, lane1_total)
        cross = crossover_length(lane["lane"], lane_width, tangent_length)

        turn1 = (stagger / 2) + cross
        turn2 = stagger
        turn3 = (stagger * 1.5) + cross
        turn4 = stagger * 2

        results.append({
            "lane": lane["lane"],
            "turn1": round4(turn1),
            "turn1_angle": format_dms(turn1 * lane["degrees_per_foot"]),
            "turn2": round4(turn2),
            "turn2_angle": format_dms(turn2 * lane["degrees_per_foot"]),
            "turn3": round4(turn3),
            "turn3_angle": format_dms(turn3 * lane["degrees_per_foot"]),
            "turn4": round4(turn4),
            "turn4_angle": format_dms(turn4 * lane["degrees_per_foot"]),
        })

    return results


def calculate_400_relay_ex1(lanes, tangent_length):
    results = []
    lane1_total = lanes[0]["total_lane_length"]

    for lane in lanes:
        stagger = lane_stagger(lane, lane1_total)

        start = stagger
        prep = start + tangent_length - 65.6166
        begin = prep + 32.8083
        center = begin + 32.8083
        finish = center + 32.8083

        results.append({
            "lane": lane["lane"],
            "start": round4(start),
            "prep": round4(prep),
            "begin": round4(begin),
            "center": round4(center),
            "finish": round4(finish),
        })

    return results


def calculate_400_relay_ex2(lanes):
    results = []
    lane1_total = lanes[0]["total_lane_length"]

    for lane in lanes:
        stagger = lane_stagger(lane, lane1_total)

        prep = 590.55 + stagger
        begin = prep + 32.8083
        center = begin + 32.8083
        finish = center + 32.8083

        results.append({
            "lane": lane["lane"],
            "prep": round4(prep),
            "begin": round4(begin),
            "center": round4(center),
            "finish": round4(finish),
        })

    return results


def calculate_400_relay_ex3(lanes):
    results = []
    lane1_total = lanes[0]["total_lane_length"]

    for lane in lanes:
        stagger = lane_stagger(lane, lane1_total)

        prep = 918.6333 + stagger
        begin = prep + 32.8083
        center = begin + 32.8083
        finish = center + 32.8083

        results.append({
            "lane": lane["lane"],
            "prep": round4(prep),
            "begin": round4(begin),
            "center": round4(center),
            "finish": round4(finish),
        })

    return results


def calculate_800_relay_ex1(lanes):
    results = []
    lane1_total = lanes[0]["total_lane_length"]

    for lane in lanes:
        stagger = lane_stagger(lane, lane1_total)

        start = stagger * 2
        prep = start + 590.55
        begin = prep + 32.8083
        center = begin + 32.8083
        finish = center + 32.8083

        results.append({
            "lane": lane["lane"],
            "start": round4(start),
            "prep": round4(prep),
            "begin": round4(begin),
            "center": round4(center),
            "finish": round4(finish),
        })

    return results


def calculate_800_relay_ex2(lanes):
    results = []
    lane1_total = lanes[0]["total_lane_length"]

    for lane in lanes:
        stagger = lane_stagger(lane, lane1_total)

        prep = 1246.7167 + (stagger * 2)
        begin = prep + 32.8083
        center = begin + 32.8083
        finish = center + 32.8083

        results.append({
            "lane": lane["lane"],
            "prep": round4(prep),
            "begin": round4(begin),
            "center": round4(center),
            "finish": round4(finish),
        })

    return results


def calculate_800_relay_ex3(lanes):
    results = []
    lane1_total = lanes[0]["total_lane_length"]

    for lane in lanes:
        stagger = lane_stagger(lane, lane1_total)

        prep = 1902.8833 + (stagger * 2)
        begin = prep + 32.8083
        center = begin + 32.8083
        finish = center + 32.8083

        results.append({
            "lane": lane["lane"],
            "prep": round4(prep),
            "begin": round4(begin),
            "center": round4(center),
            "finish": round4(finish),
        })

    return results


def calculate_1600_relay_ex1(lanes, lane_width, tangent_length):
    results = []
    lane1_total = lanes[0]["total_lane_length"]

    for lane in lanes:
        start = stagger_turn3(lane, lane1_total, lane_width, tangent_length)

        begin = 1279.525 + start
        center = begin + 32.8083
        finish = center + 32.8083

        results.append({
            "lane": lane["lane"],
            "start": round4(start),
            "begin": round4(begin),
            "center": round4(center),
            "finish": round4(finish),
        })

    return results


def calculate_1600_relay_ex2_ex3(lanes):
    results = []
    lane1_total = lanes[0]["total_lane_length"]

    for lane in lanes:
        stagger = lane_stagger(lane, lane1_total)

        begin = 1279.525 + stagger
        center = begin + 32.8083
        finish = center + 32.8083

        results.append({
            "lane": lane["lane"],
            "begin": round4(begin),
            "center": round4(center),
            "finish": round4(finish),
        })

    return results


def calculate_200_meter_starts(lanes):
    results = calculate_400_relay_ex2(lanes)
    return [{"lane": row["lane"], "start": row["center"]} for row in results]


def calculate_300_hurdles(lanes, tangent_length):
    results = []

    start_to_h1 = 147.6375
    between = 114.8292

    relay_ex1 = calculate_400_relay_ex1(lanes, tangent_length)

    for row in relay_ex1:
        start = row["center"]

        hurdles = []
        current = start + start_to_h1

        for _ in range(8):
            hurdles.append(round4(current))
            current += between

        results.append({
            "lane": row["lane"],
            "start": round4(start),
            "hurdles": hurdles,
        })

    return results


def calculate_400_hurdles(lanes):
    results = []
    lane1_total = lanes[0]["total_lane_length"]

    start_to_h1 = 147.6375
    between = 114.8292

    for lane in lanes:
        stagger = lane_stagger(lane, lane1_total)

        start = stagger
        hurdles = []
        current = start + start_to_h1

        for _ in range(10):
            hurdles.append(round4(current))
            current += between

        results.append({
            "lane": lane["lane"],
            "start": round4(start),
            "hurdles": hurdles,
        })

    return results


def calculate_steeplechase():
    sc2000 = {
        "start": ("PT#3", off(-45.1767)),
        "h1": ("PT#3", '28°17\'34"'),
        "h2": ("PT#3", '151°59\'13"'),
        "h3": ("PT#1", off(-75.2263)),
        "h4": ("PT#2", off(75.8164)),
        "finish": ("PT#3", off(0.0)),
    }

    sc3000 = {
        "start": ("PT#1", off(-63.2467)),
        "h1": ("PT#3", '28°17\'34"'),
        "h2": ("PT#3", '151°59\'13"'),
        "h3": ("PT#1", off(-75.2263)),
        "h4": ("PT#2", off(75.8164)),
        "finish": ("PT#3", off(0.0)),
    }

    return sc2000, sc3000


if __name__ == "__main__":

    lanes = calculate_lanes(radius, tangent_length, lane_width, number_of_lanes, curb_present)

    print(f"\nJOB NAME: {job_name}")
    print(f"FINISH OFFSET: {finish_offset}")

    print("\nLANE LENGTHS")
    for lane in lanes:
        print(lane["lane"], lane["path_measurement"], lane["length_of_arc"], lane["length_one_degree"], lane["degrees_per_foot"], lane["total_lane_length"])

    print("\nPOINT TO POINT LENGTHS")
    for row in calculate_point_to_point(lanes, tangent_length):
        print(row["lane"], row["pc1_to_pc2"], row["pc1_to_pc3"], row["pc1_to_pc4"], row["pc1_to_pc1"])

    print("\nDISTANCE GREATER THAN LANE ONE")
    for row in calculate_distance_greater_than_lane_one(lanes):
        print(row["lane"], row["turn1"], row["turn2"], row["turn3"], row["turn4"])

    print("\nCROSSOVER LENGTHS")
    for row in calculate_crossover_lengths(lanes, lane_width, tangent_length):
        print(row["lane"], row["distance"], row["turn1_angle"], row["turn3_angle"])

    print("\nSTAGGER STARTS")
    for row in calculate_stagger_starts(lanes, lane_width, tangent_length):
        print(row["lane"], off(row["turn1"]), row["turn1_angle"], off(row["turn2"]), row["turn2_angle"], off(row["turn3"]), row["turn3_angle"], off(row["turn4"]), row["turn4_angle"])

    print("\n400 RELAY ex1")
    for row in calculate_400_relay_ex1(lanes, tangent_length):
        lane = lanes[row["lane"] - 1]
        print(row["lane"], mark_with_angle(row["start"], lane), mark_with_angle(row["prep"], lane), mark_with_angle(row["begin"], lane), mark_with_angle(row["center"], lane), mark_with_angle(row["finish"], lane))

    print("\n400 RELAY ex2")
    for row in calculate_400_relay_ex2(lanes):
        lane = lanes[row["lane"] - 1]
        print(row["lane"], mark_to_pt3(row["prep"], lane), mark_to_pt3(row["begin"], lane), mark_to_pt3(row["center"], lane), mark_to_pt3(row["finish"], lane))

    print("\n400 RELAY ex3")
    for row in calculate_400_relay_ex3(lanes):
        lane = lanes[row["lane"] - 1]
        print(row["lane"], mark_with_angle(row["prep"], lane), mark_with_angle(row["begin"], lane), mark_with_angle(row["center"], lane), mark_with_angle(row["finish"], lane))

    print("\n800 RELAY ex1")
    for row in calculate_800_relay_ex1(lanes):
        lane = lanes[row["lane"] - 1]
        print(row["lane"], mark_with_angle(row["start"], lane), mark_to_pt3(row["prep"], lane), mark_to_pt3(row["begin"], lane), mark_to_pt3(row["center"], lane), mark_to_pt3(row["finish"], lane))

    print("\n800 RELAY ex2")
    for row in calculate_800_relay_ex2(lanes):
        lane = lanes[row["lane"] - 1]
        print(row["lane"], mark_to_pt1(row["prep"], lane), mark_to_pt1(row["begin"], lane), mark_to_pt1(row["center"], lane), mark_to_pt1(row["finish"], lane))

    print("\n800 RELAY ex3")
    for row in calculate_800_relay_ex3(lanes):
        lane = lanes[row["lane"] - 1]
        print(row["lane"], mark_to_pt3(row["prep"], lane), mark_to_pt3(row["begin"], lane), mark_to_pt3(row["center"], lane), mark_to_pt3(row["finish"], lane))

    print("\n1600 RELAY ex1")
    for row in calculate_1600_relay_ex1(lanes, lane_width, tangent_length):
        lane = lanes[row["lane"] - 1]
        print(row["lane"], mark_with_angle(row["start"], lane), mark_to_pt1(row["begin"], lane), mark_to_pt1(row["center"], lane), mark_to_pt1(row["finish"], lane))

    print("\n1600 RELAY ex2/ex3")
    for row in calculate_1600_relay_ex2_ex3(lanes):
        lane = lanes[row["lane"] - 1]
        print(row["lane"], mark_to_pt1(row["begin"], lane), mark_to_pt1(row["center"], lane), mark_to_pt1(row["finish"], lane))

    print("\n200 METER STARTS")
    for row in calculate_200_meter_starts(lanes):
        lane = lanes[row["lane"] - 1]
        print(row["lane"], mark_with_angle(row["start"], lane))

    if hurdles_300_present:
        print("\n300 HURDLES")
        for row in calculate_300_hurdles(lanes, tangent_length):
            lane = lanes[row["lane"] - 1]
            values = [mark_nearest_pc(row["start"], lane)]
            values += [mark_nearest_pc(h, lane) for h in row["hurdles"]]
            print(row["lane"], *values)

    if hurdles_400_present:
        print("\n400 HURDLES")
        for row in calculate_400_hurdles(lanes):
            lane = lanes[row["lane"] - 1]
            values = [mark_nearest_pc(row["start"], lane)]
            values += [mark_nearest_pc(h, lane) for h in row["hurdles"]]
            print(row["lane"], *values)

    if steeplechase_present:
        sc2000, sc3000 = calculate_steeplechase()

        print("\n2000 METER STEEPLECHASE")
        print("START", format_mark(sc2000["start"]))
        print("HURDLE 1", format_mark(sc2000["h1"]))
        print("HURDLE 2", format_mark(sc2000["h2"]))
        print("HURDLE 3", format_mark(sc2000["h3"]))
        print("HURDLE 4", format_mark(sc2000["h4"]))
        print("FINISH", format_mark(sc2000["finish"]))

        print("\n3000 METER STEEPLECHASE")
        print("START", format_mark(sc3000["start"]))
        print("HURDLE 1", format_mark(sc3000["h1"]))
        print("HURDLE 2", format_mark(sc3000["h2"]))
        print("HURDLE 3", format_mark(sc3000["h3"]))
        print("HURDLE 4", format_mark(sc3000["h4"]))
        print("FINISH", format_mark(sc3000["finish"]))