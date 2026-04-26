import streamlit as st
import pandas as pd
import track_calc2 as backend
import streamlit as st

PASSWORD = "track123"  # change this

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        pwd = st.text_input("Enter Password", type="password")

        if pwd == PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.stop()

check_password()

st.set_page_config(layout="wide")
st.title("Track Marking Calculator")


# -----------------------------
# HELPERS
# -----------------------------

def parse_float(label, default):
    value = st.sidebar.text_input(label, default)
    try:
        return float(value)
    except ValueError:
        st.sidebar.error(f"{label} must be a number.")
        st.stop()


def stacked_mark(value):
    value = str(value)
    parts = value.split(" ", 1)

    if len(parts) == 2:
        return f"{parts[0]}<br>{parts[1]}"

    return value


def show_table(rows):
    df = pd.DataFrame(rows)

    html = df.to_html(
        escape=False,
        index=False
    )

    st.markdown(
        html,
        unsafe_allow_html=True
    )


# -----------------------------
# SIDEBAR INPUTS
# -----------------------------

st.sidebar.header("Track Parameters")

job_name = st.sidebar.text_input("Job Name", "")

radius = parse_float("Radius", "103.776")
tangent_length = parse_float("Straight Length", "328.0832")
lane_width = parse_float("Lane Width", "3.5")

number_of_lanes = st.sidebar.number_input(
    "Lanes",
    min_value=1,
    max_value=20,
    value=8,
    step=1
)

finish_offset = parse_float("Finish Offset", "0.0")

# IMPORTANT:
# Your backend uses finish_offset globally inside off()
backend.finish_offset = finish_offset

# Create placeholder first so Lane 1 distance appears above curb checkbox
lane_1_placeholder = st.sidebar.empty()

curb_present = st.sidebar.checkbox("Curb Present", value=False)

preview_lanes = backend.calculate_lanes(
    radius,
    tangent_length,
    lane_width,
    number_of_lanes,
    curb_present
)

lane_1_distance = preview_lanes[0]["total_lane_length"]

lane_1_placeholder.markdown("### Track Info")
lane_1_placeholder.metric("Lane 1 Lap Distance", lane_1_distance)

st.sidebar.divider()

sections = {
    "Lane Lengths": st.sidebar.checkbox("Lane Lengths", False),
    "Point to Point": st.sidebar.checkbox("Point to Point", False),
    "Distance > Lane 1": st.sidebar.checkbox("Distance > Lane 1", False),
    "Crossover Lengths": st.sidebar.checkbox("Crossover Lengths", True),
    "Stagger Starts": st.sidebar.checkbox("Stagger Starts", True),
    "400 Relay": st.sidebar.checkbox("400 Relay", True),
    "800 Relay": st.sidebar.checkbox("800 Relay", True),
    "1600 Relay": st.sidebar.checkbox("1600 Relay", True),
    "200 Starts": st.sidebar.checkbox("200 Starts", True),
    "300 Hurdles": st.sidebar.checkbox("300 Hurdles", True),
    "400 Hurdles": st.sidebar.checkbox("400 Hurdles", True),
    "Steeplechase": st.sidebar.checkbox("Steeplechase", False),
}

run = st.sidebar.button("Calculate")


# -----------------------------
# RUN CALCULATION
# -----------------------------

if run:

    lanes = backend.calculate_lanes(
        radius,
        tangent_length,
        lane_width,
        number_of_lanes,
        curb_present
    )

    st.header(f"JOB: {job_name}")
    st.caption(f"Finish Offset: {finish_offset}")

    active_sections = [k for k, v in sections.items() if v]
    tabs = st.tabs(active_sections)

    tab_index = 0

    # -----------------------------
    # LANE LENGTHS
    # -----------------------------
    if sections["Lane Lengths"]:
        with tabs[tab_index]:

            data = pd.DataFrame(lanes)

            data = data.rename(columns={
                "lane": "Lane",
                "path_measurement": "Path Measurement",
                "length_of_arc": "Arc Length",
                "length_one_degree": "Length of 1 Degree",
                "degrees_per_foot": "Degrees per Foot",
                "total_lane_length": "Lap 1 Distance",
            })

            st.dataframe(data, use_container_width=True, hide_index=True)

        tab_index += 1

    # -----------------------------
    # POINT TO POINT
    # -----------------------------
    if sections["Point to Point"]:
        with tabs[tab_index]:
            data = pd.DataFrame(
                backend.calculate_point_to_point(lanes, tangent_length)
            )

            data = data.rename(columns={
                "lane": "Lane",
                "pc1_to_pc2": "PC1 to PC2",
                "pc1_to_pc3": "PC1 to PC3",
                "pc1_to_pc4": "PC1 to PC4",
                "pc1_to_pc1": "PC1 to PC1",
            })

            st.dataframe(data, use_container_width=True, hide_index=True)

        tab_index += 1

    # -----------------------------
    # DISTANCE GREATER THAN LANE 1
    # -----------------------------
    if sections["Distance > Lane 1"]:
        with tabs[tab_index]:
            data = pd.DataFrame(
                backend.calculate_distance_greater_than_lane_one(lanes)
            )

            data = data.rename(columns={
                "lane": "Lane",
                "turn1": "Turn 1",
                "turn2": "Turn 2",
                "turn3": "Turn 3",
                "turn4": "Turn 4",
            })

            st.dataframe(data, use_container_width=True, hide_index=True)

        tab_index += 1

    # -----------------------------
    # CROSSOVER LENGTHS
    # -----------------------------
    if sections["Crossover Lengths"]:
        with tabs[tab_index]:
            data = pd.DataFrame(
                backend.calculate_crossover_lengths(
                    lanes,
                    lane_width,
                    tangent_length
                )
            )

            data = data.rename(columns={
                "lane": "Lane",
                "distance": "Distance",
                "turn1_angle": "Turn 1 Angle",
                "turn3_angle": "Turn 3 Angle",
            })

            st.dataframe(data, use_container_width=True, hide_index=True)

        tab_index += 1

    # -----------------------------
    # STAGGER STARTS
    # -----------------------------
    if sections["Stagger Starts"]:
        with tabs[tab_index]:
            rows = []

            for r in backend.calculate_stagger_starts(
                lanes,
                lane_width,
                tangent_length
            ):
                lane = lanes[r["lane"] - 1]

                rows.append({
                    "Lane": r["lane"],
                    "Turn 1": stacked_mark(backend.mark_with_angle(r["turn1"], lane)),
                    "Turn 2": stacked_mark(backend.mark_with_angle(r["turn2"], lane)),
                    "Turn 3": stacked_mark(backend.mark_with_angle(r["turn3"], lane)),
                    "Turn 4": stacked_mark(backend.mark_with_angle(r["turn4"], lane)),
                })

            show_table(rows)

        tab_index += 1

    # -----------------------------
    # 400 RELAY
    # -----------------------------
    if sections["400 Relay"]:
        with tabs[tab_index]:

            st.subheader("Exchange 1")

            rows = []
            for r in backend.calculate_400_relay_ex1(lanes, tangent_length):
                lane = lanes[r["lane"] - 1]
                rows.append({
                    "Lane": r["lane"],
                    "Start": stacked_mark(backend.mark_with_angle(r["start"], lane)),
                    "Prep": stacked_mark(backend.mark_with_angle(r["prep"], lane)),
                    "Begin": stacked_mark(backend.mark_with_angle(r["begin"], lane)),
                    "Center": stacked_mark(backend.mark_with_angle(r["center"], lane)),
                    "Finish": stacked_mark(backend.mark_with_angle(r["finish"], lane)),
                })

            show_table(rows)

            st.subheader("Exchange 2")

            rows = []
            for r in backend.calculate_400_relay_ex2(lanes):
                lane = lanes[r["lane"] - 1]
                rows.append({
                    "Lane": r["lane"],
                    "Prep": stacked_mark(backend.mark_to_pt3(r["prep"], lane)),
                    "Begin": stacked_mark(backend.mark_to_pt3(r["begin"], lane)),
                    "Center": stacked_mark(backend.mark_to_pt3(r["center"], lane)),
                    "Finish": stacked_mark(backend.mark_to_pt3(r["finish"], lane)),
                })

            show_table(rows)

            st.subheader("Exchange 3")

            rows = []
            for r in backend.calculate_400_relay_ex3(lanes):
                lane = lanes[r["lane"] - 1]
                rows.append({
                    "Lane": r["lane"],
                    "Prep": stacked_mark(backend.mark_with_angle(r["prep"], lane)),
                    "Begin": stacked_mark(backend.mark_with_angle(r["begin"], lane)),
                    "Center": stacked_mark(backend.mark_with_angle(r["center"], lane)),
                    "Finish": stacked_mark(backend.mark_with_angle(r["finish"], lane)),
                })

            show_table(rows)

        tab_index += 1

    # -----------------------------
    # 800 RELAY
    # -----------------------------
    if sections["800 Relay"]:
        with tabs[tab_index]:

            st.subheader("Exchange 1")

            rows = []
            for r in backend.calculate_800_relay_ex1(lanes):
                lane = lanes[r["lane"] - 1]
                rows.append({
                    "Lane": r["lane"],
                    "Start": stacked_mark(backend.mark_with_angle(r["start"], lane)),
                    "Prep": stacked_mark(backend.mark_to_pt3(r["prep"], lane)),
                    "Begin": stacked_mark(backend.mark_to_pt3(r["begin"], lane)),
                    "Center": stacked_mark(backend.mark_to_pt3(r["center"], lane)),
                    "Finish": stacked_mark(backend.mark_to_pt3(r["finish"], lane)),
                })

            show_table(rows)

            st.subheader("Exchange 2")

            rows = []
            for r in backend.calculate_800_relay_ex2(lanes):
                lane = lanes[r["lane"] - 1]
                rows.append({
                    "Lane": r["lane"],
                    "Prep": stacked_mark(backend.mark_to_pt1(r["prep"], lane)),
                    "Begin": stacked_mark(backend.mark_to_pt1(r["begin"], lane)),
                    "Center": stacked_mark(backend.mark_to_pt1(r["center"], lane)),
                    "Finish": stacked_mark(backend.mark_to_pt1(r["finish"], lane)),
                })

            show_table(rows)

            st.subheader("Exchange 3")

            rows = []
            for r in backend.calculate_800_relay_ex3(lanes):
                lane = lanes[r["lane"] - 1]
                rows.append({
                    "Lane": r["lane"],
                    "Prep": stacked_mark(backend.mark_to_pt3(r["prep"], lane)),
                    "Begin": stacked_mark(backend.mark_to_pt3(r["begin"], lane)),
                    "Center": stacked_mark(backend.mark_to_pt3(r["center"], lane)),
                    "Finish": stacked_mark(backend.mark_to_pt3(r["finish"], lane)),
                })

            show_table(rows)

        tab_index += 1

    # -----------------------------
    # 1600 RELAY
    # -----------------------------
    if sections["1600 Relay"]:
        with tabs[tab_index]:

            st.subheader("Exchange 1")

            rows = []
            for r in backend.calculate_1600_relay_ex1(
                lanes,
                lane_width,
                tangent_length
            ):
                lane = lanes[r["lane"] - 1]
                rows.append({
                    "Lane": r["lane"],
                    "Start": stacked_mark(backend.mark_with_angle(r["start"], lane)),
                    "Begin": stacked_mark(backend.mark_to_pt1(r["begin"], lane)),
                    "Center": stacked_mark(backend.mark_to_pt1(r["center"], lane)),
                    "Finish": stacked_mark(backend.mark_to_pt1(r["finish"], lane)),
                })

            show_table(rows)

            st.subheader("Exchange 2 / Exchange 3")

            rows = []
            for r in backend.calculate_1600_relay_ex2_ex3(lanes):
                lane = lanes[r["lane"] - 1]
                rows.append({
                    "Lane": r["lane"],
                    "Begin": stacked_mark(backend.mark_to_pt1(r["begin"], lane)),
                    "Center": stacked_mark(backend.mark_to_pt1(r["center"], lane)),
                    "Finish": stacked_mark(backend.mark_to_pt1(r["finish"], lane)),
                })

            show_table(rows)

        tab_index += 1

    # -----------------------------
    # 200 STARTS
    # -----------------------------
    if sections["200 Starts"]:
        with tabs[tab_index]:

            rows = []
            for r in backend.calculate_200_meter_starts(lanes):
                lane = lanes[r["lane"] - 1]
                rows.append({
                    "Lane": r["lane"],
                    "Start": stacked_mark(backend.mark_with_angle(r["start"], lane)),
                })

            show_table(rows)

        tab_index += 1

    # -----------------------------
    # 300 HURDLES
    # -----------------------------
    if sections["300 Hurdles"]:
        with tabs[tab_index]:

            rows = []
            for r in backend.calculate_300_hurdles(lanes, tangent_length):
                lane = lanes[r["lane"] - 1]

                row = {
                    "Lane": r["lane"],
                    "Start": stacked_mark(backend.mark_nearest_pc(r["start"], lane)),
                }

                for i, h in enumerate(r["hurdles"]):
                    row[f"H{i + 1}"] = stacked_mark(
                        backend.mark_nearest_pc(h, lane)
                    )

                rows.append(row)

            show_table(rows)

        tab_index += 1

    # -----------------------------
    # 400 HURDLES
    # -----------------------------
    if sections["400 Hurdles"]:
        with tabs[tab_index]:

            rows = []
            for r in backend.calculate_400_hurdles(lanes):
                lane = lanes[r["lane"] - 1]

                row = {
                    "Lane": r["lane"],
                    "Start": stacked_mark(backend.mark_nearest_pc(r["start"], lane)),
                }

                for i, h in enumerate(r["hurdles"]):
                    row[f"H{i + 1}"] = stacked_mark(
                        backend.mark_nearest_pc(h, lane)
                    )

                rows.append(row)

            show_table(rows)

        tab_index += 1

    # -----------------------------
    # STEEPLECHASE
    # -----------------------------
    if sections["Steeplechase"]:
        with tabs[tab_index]:

            sc2000, sc3000 = backend.calculate_steeplechase()

            st.subheader("2000m")
            st.write(sc2000)

            st.subheader("3000m")
            st.write(sc3000)