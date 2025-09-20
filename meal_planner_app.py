import streamlit as st
from datetime import datetime
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io
import math
from collections import defaultdict
import json

# --- App Configuration ---
st.set_page_config(
    page_title="Weekly Meal Planner",
    page_icon="🍲",
    layout="wide"
)

date_today = datetime.today().strftime('%Y-%m-%d')

# --- Helper Functions ---

def load_meals(filepath="meals.json"):
    """Loads the meal database from a JSON file."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"Error: The `{filepath}` file was not found. Please create it in the same directory as the script.")
        return []
    except json.JSONDecodeError:
        st.error(f"Error: The `{filepath}` file is not a valid JSON. Please check its syntax.")
        return []

def get_meal_by_name(name, meals_db):
    """Finds a meal in the MEALS list by its name."""
    for meal in meals_db:
        if meal['name'] == name:
            return meal
    return None

def create_meal_plan_image(plan, prep_list):
    """Generates an image of the weekly meal plan timetable with meal prep notes."""
    width, height = 1800, 1200  # Increased height for notes section
    bg_color = "white"
    font_color = "black"
    difficulty_color = "#555555"
    header_color = "#F0F2F6"
    line_color = "#DDDDDD"

    image = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(image)

    try:
        # Use a built-in font or specify a path to a .ttf file
        title_font = ImageFont.truetype("arial.ttf", 50)
        header_font = ImageFont.truetype("arialbd.ttf", 35)
        cell_font = ImageFont.truetype("arial.ttf", 30)
        difficulty_font = ImageFont.truetype("arial.ttf", 24)
        notes_title_font = ImageFont.truetype("arialbd.ttf", 32)
        notes_font = ImageFont.truetype("arial.ttf", 28)
    except IOError:
        # Fallback to default font if arial is not found
        title_font = ImageFont.load_default()
        header_font = ImageFont.load_default()
        cell_font = ImageFont.load_default()
        difficulty_font = ImageFont.load_default()
        notes_title_font = ImageFont.load_default()
        notes_font = ImageFont.load_default()

    # Title
    draw.text((width/2, 60), "Weekly Meal Plan", fill=font_color, font=title_font, anchor="ms")

    # Grid setup
    days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    meals_of_day = ["Breakfast", "Lunch", "Dinner"]
    
    start_x, start_y = 50, 150
    grid_height = 750 # Height for the meal grid itself
    col_width = (width - 2 * start_x) / (len(days) + 0.5)
    row_height = grid_height / (len(meals_of_day) + 1)
    
    # Draw header row for days
    for i, day in enumerate(days):
        x = start_x + col_width * (i + 0.5)
        draw.rectangle(
            [x, start_y, x + col_width, start_y + row_height],
            fill=header_color
        )
        draw.text((x + col_width/2, start_y + row_height/2), day, fill=font_color, font=header_font, anchor="mm")

    # Draw header column for meal types
    for j, meal_type in enumerate(meals_of_day):
        y = start_y + row_height * (j + 1)
        draw.rectangle(
            [start_x, y, start_x + col_width * 0.5, y + row_height],
            fill=header_color
        )
        draw.text((start_x + col_width*0.25, y + row_height/2), meal_type, fill=font_color, font=header_font, anchor="mm")

    # Draw grid lines and fill cells
    grid_bottom = start_y + row_height * (len(meals_of_day) + 1)
    for i in range(len(days) + 1):
        x = start_x + col_width * (i + 0.5)
        draw.line([x, start_y, x, grid_bottom], fill=line_color, width=2)
    
    for j in range(len(meals_of_day) + 2):
        y = start_y + row_height * j
        draw.line([start_x, y, width - start_x, y], fill=line_color, width=2)

    # Helper for wrapping text
    def wrap_text(text, font, max_width):
        lines = []
        words = text.split(' ')
        while words:
            line = ''
            while words and font.getbbox(line + words[0])[2] <= max_width:
                line += words.pop(0) + ' '
            if not line and words: # Handle single very long word
                line = words.pop(0) + ' '
            lines.append(line.strip())
        return lines

    # Fill in the plan
    cell_padding = 15
    for i, day in enumerate(days):
        for j, meal_type in enumerate(meals_of_day):
            meal_info = plan.get(day, {}).get(meal_type)
            if meal_info and 'name' in meal_info:
                meal_name = meal_info['name']
                difficulty = f"({meal_info['difficulty']})"
                
                x = start_x + col_width * (i + 0.5) + cell_padding
                y = start_y + row_height * (j + 1) + cell_padding
                
                # Wrap and draw meal name
                wrapped_name_lines = wrap_text(meal_name, cell_font, col_width - (2 * cell_padding))
                for line in wrapped_name_lines:
                    draw.text((x, y), line, fill=font_color, font=cell_font)
                    y += cell_font.getbbox(line)[3] + 5
                
                draw.text((x, y + 5), difficulty, fill=difficulty_color, font=difficulty_font)

    # Add Meal Prep Notes section at the bottom
    if prep_list:
        notes_y_start = grid_bottom + 50
        draw.text((start_x, notes_y_start), "🍳 Meal Prep Notes", font=notes_title_font, fill=font_color)
        
        notes_text = "The following meals can be prepared in advance: " + ", ".join(prep_list)
        wrapped_notes = wrap_text(notes_text, notes_font, width - (2 * start_x))
        
        notes_y = notes_y_start + 50
        for line in wrapped_notes:
            draw.text((start_x, notes_y), line, font=notes_font, fill=font_color)
            notes_y += notes_font.getbbox(line)[3] + 10

    return image


# --- Streamlit App UI ---

# Load meal data from the external file
MEALS = load_meals()

st.title("🍲 Weekly Meal Planner")

if MEALS:
    st.write("Choose your meals for the week, and I'll generate a shopping list and a downloadable timetable for you.")

    # Display the meal database in an expander
    with st.expander("📚 View Available Meals & Recipes"):
        for meal in MEALS:
            meal_prep_text = "Yes" if meal.get('meal_prep', False) else "No"
            is_salad_text = "Yes" if meal.get('is_salad', False) else "No"
            st.subheader(f"{meal['name']} ({', '.join(meal['type'])})")
            st.markdown(f"**Difficulty:** {meal['difficulty']} | **Salad:** {is_salad_text} | **Can be Meal-Prepped:** {meal_prep_text}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Ingredients:**")
                for ing in meal['ingredients']:
                    st.write(f"- {ing['item']}: {ing['quantity']} {ing['unit']}")
            with col2:
                st.markdown("**Recipe:**")
                st.write(meal['recipe'])
            st.markdown("---")

    st.header("🗓️ Plan Your Week")

    # Initialize session state for storing selections
    if 'plan' not in st.session_state:
        st.session_state.plan = {}

    # Create timetable UI
    days_of_week = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    meal_types = ["Breakfast", "Lunch", "Dinner"]
    cols = st.columns(len(days_of_week))

    for i, day in enumerate(days_of_week):
        with cols[i]:
            st.subheader(day)
            if day not in st.session_state.plan:
                st.session_state.plan[day] = {}
                
            for meal_type in meal_types:
                st.markdown(f"**{meal_type}**")
                meal_options = ["-"] + [m['name'] for m in MEALS if meal_type in m['type'] and not m.get('is_salad', False)]
                
                meal_key = f"{day}_{meal_type}_meal"
                people_key = f"{day}_{meal_type}_people"

                meal_col, people_col = st.columns([3, 1])

                with meal_col:
                    selected_meal = st.selectbox(f"Select {meal_type}", options=meal_options, key=meal_key, label_visibility="collapsed")
                
                with people_col:
                    num_people = st.number_input(f"People for {meal_type}", min_value=1, value=1, step=1, key=people_key, label_visibility="collapsed")
                
                if selected_meal != "-":
                    st.session_state.plan.setdefault(day, {})[meal_type] = {'name': selected_meal, 'people': num_people}
                elif meal_type in st.session_state.plan.get(day, {}):
                    del st.session_state.plan[day][meal_type]

                # Add salad slot for Lunch and Dinner
                if meal_type in ["Lunch", "Dinner"]:
                    salad_options = ["-"] + [m['name'] for m in MEALS if m.get('is_salad', False)]
                    salad_key = f"{day}_{meal_type}_salad"
                    
                    selected_salad = st.selectbox("Side Salad", options=salad_options, key=salad_key, help="Optional side salad")
                    
                    if selected_salad != "-":
                         st.session_state.plan.setdefault(day, {}).setdefault(meal_type, {})['salad'] = selected_salad
                    elif 'salad' in st.session_state.plan.get(day, {}).get(meal_type, {}):
                        del st.session_state.plan[day][meal_type]['salad']


    # --- Generate Plan & Shopping List ---
    st.header("✅ Generate Your Plan")

    if st.button("Generate Shopping List & Timetable"):
        
        shopping_list = defaultdict(lambda: {'quantity': 0, 'units': set()})
        final_plan = {}
        prep_list = []
        is_plan_empty = True

        def add_ingredients_to_list(meal_name, num_people):
            meal_details = get_meal_by_name(meal_name, MEALS)
            if not meal_details: return

            if meal_details.get('meal_prep', False):
                prep_list.append(meal_details['name'])

            default_portions = meal_details.get('default_portions', 1)
            scaling_factor = num_people / default_portions
            
            for ingredient in meal_details['ingredients']:
                item = ingredient['item']
                scaled_quantity = ingredient['quantity'] * scaling_factor
                shopping_list[item]['quantity'] += scaled_quantity
                shopping_list[item]['units'].add(ingredient['unit'])

        for day, meals in st.session_state.plan.items():
            final_plan[day] = {}
            for meal_type, selection in meals.items():
                
                if 'name' in selection:
                    is_plan_empty = False
                    main_meal_name = selection['name']
                    num_people = selection['people']
                    main_meal_details = get_meal_by_name(main_meal_name, MEALS)
                    if main_meal_details:
                        final_plan.setdefault(day, {})[meal_type] = {
                            'name': main_meal_details['name'],
                            'difficulty': main_meal_details['difficulty']
                        }
                        add_ingredients_to_list(main_meal_name, num_people)

                if 'salad' in selection:
                    is_plan_empty = False
                    salad_name = selection['salad']
                    num_people_salad = selection.get('people', 1) # Assume salad for same num people
                    add_ingredients_to_list(salad_name, num_people_salad)

        if is_plan_empty:
            st.warning("Your meal plan is empty! Please select at least one meal.")
        else:
            st.balloons()
            
            st.subheader("🛒 Your Shopping List")
            shopping_df_data = []
            for item, data in sorted(shopping_list.items()):
                final_quantity = math.ceil(data['quantity'] * 100) / 100
                units_str = ", ".join(sorted(list(data['units'])))
                shopping_df_data.append([item, final_quantity, units_str])

            shopping_df = pd.DataFrame(shopping_df_data, columns=["Ingredient", "Quantity", "Unit"])
            st.dataframe(shopping_df, use_container_width=True, hide_index=True)
            
            shopping_list_text = "Your Shopping List\n------------------\n"
            for item, quantity, unit in shopping_df_data:
                shopping_list_text += f"- {item}: {quantity} {unit}\n"
            
            st.download_button("Download Shopping List as TXT", shopping_list_text, f"shopping_list_{date_today}.txt", "text/plain")

            st.subheader("🖼️ Your Timetable")
            unique_prep_list = sorted(list(set(prep_list)))
            plan_image = create_meal_plan_image(final_plan, unique_prep_list)
            
            img_byte_arr = io.BytesIO()
            plan_image.save(img_byte_arr, format='PNG')
            
            st.image(plan_image)
            st.download_button("Download Timetable as PNG", img_byte_arr.getvalue(), f"meal_plan_{date_today}.png", "image/png")
            
            if prep_list:
                st.subheader("🍳 Meal Prep Notes")
                st.write("The following meals can be prepared in advance:")
                for meal_name in sorted(list(set(prep_list))):
                    st.markdown(f"- {meal_name}")

