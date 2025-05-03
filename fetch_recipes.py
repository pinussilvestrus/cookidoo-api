#!/usr/bin/env python3
"""Example script for cookidoo-api."""

import asyncio
from datetime import datetime
import logging
import os
import sys
from datetime import timedelta

import aiohttp
from dotenv import load_dotenv

from cookidoo_api import Cookidoo
from cookidoo_api.helpers import (
    get_country_options,
    get_language_options,
    get_localization_options,
)
from cookidoo_api.types import (
    CookidooAdditionalItem,
    CookidooConfig,
    CookidooIngredientItem,
)

load_dotenv()

# Configure the root logger
logging.basicConfig(
    level=logging.DEBUG,  # Set the logging level (DEBUG, INFO, WARNING, etc.)
    format="%(asctime)s [%(levelname)8s] %(name)s:%(lineno)s %(message)s",  # Format of the log messages
    handlers=[  # Specify the handlers for the logger
        logging.StreamHandler(sys.stdout)  # Output to stdout
    ],
)

async def main():
    """Run main example function."""
    async with aiohttp.ClientSession() as session:
        # Show all country_codes, languages and some localizations
        _country_codes = await get_country_options()
        _languages = await get_language_options()
        _localizations_ch = await get_localization_options(country="ch")
        _localizations_en = await get_localization_options(language="en")

        # Create Cookidoo instance with email and password
        cookidoo = Cookidoo(
            session,
            cfg=CookidooConfig(
                email=os.environ["EMAIL"],
                password=os.environ["PASSWORD"],
                localization=(
                    await get_localization_options(country="ie", language="en-GB")
                )[0],
            ),
        )
        # Login
        await cookidoo.login()
        await cookidoo.refresh_token()

        async def get_all_recipes_since_date(cookidoo, start_date):
          """Retrieve all recipes cooked since a given date."""
          current_date = datetime.now().date()
          all_recipes = []

          while start_date <= current_date:
            recipes = await cookidoo.get_recipes_in_calendar_week(start_date)
            all_recipes.extend(recipes)
            start_date += timedelta(weeks=1)

          flat_recipes = [
            recipe
            for calendar_day in all_recipes
            for recipe in calendar_day.recipes
          ]
          return flat_recipes


        async def count_total_recipes(flat_recipes, start_date):
          """Count the total number of recipes cooked since a given date."""
          total_recipes = len(flat_recipes)
          print(f"Total number of recipes on calendar cooked since {start_date}: {total_recipes}")
          return total_recipes


        async def get_most_used_ingredients(cookidoo, flat_recipes, top_n=10):
          """Get the most used ingredients from the recipes."""
          ingredient_count = {}

          for recipe in flat_recipes:
            recipe_details = await cookidoo.get_recipe_details(recipe.id)
            for ingredient in recipe_details.ingredients:
              print(f"Processing ingredient: {ingredient}")
              ingredient_name = ingredient.name
              ingredient_count[ingredient_name] = ingredient_count.get(ingredient_name, 0) + 1

          sorted_ingredients = sorted(ingredient_count.items(), key=lambda x: x[1], reverse=True)

          print(f"Top {top_n} most used ingredients:")
          for i, (ingredient, count) in enumerate(sorted_ingredients[:top_n], start=1):
            print(f"{i}. {ingredient}: {count} uses")

        async def calculate_total_salt_usage(cookidoo, flat_recipes):
          """Calculate the total amount of TL (Teelöffel) Salz used."""
          total_salt_tl = 0.0

          for recipe in flat_recipes:
            recipe_details = await cookidoo.get_recipe_details(recipe.id)
            for ingredient in recipe_details.ingredients:
              if ingredient.name.lower() == "salz" and "TL" in ingredient.description:
                try:
                    # Extract the numeric value from the description
                    salt_amount = float(ingredient.description.split(" ")[0])
                    total_salt_tl += salt_amount
                except (ValueError, IndexError):
                    logging.warning(f"Could not parse salt amount from: {ingredient.description}")

          print(f"Total amount of TL Salz used: {total_salt_tl} TL")
          return total_salt_tl
        
        async def calculate_total_cooking_time(cookidoo, flat_recipes):
          """Calculate the total cooking time of all recipes."""
          total_cooking_time = 0

          for recipe in flat_recipes:
            recipe_details = await cookidoo.get_recipe_details(recipe.id)
            if recipe_details.total_time:
              total_cooking_time += recipe_details.total_time

            total_cooking_time_hours = total_cooking_time / 3600
            print(f"Total cooking time for all recipes: {total_cooking_time_hours:.2f} hours")
          return total_cooking_time
        

        async def get_top_recipe_categories(cookidoo, flat_recipes, top_n=10):
          """Calculate the top recipe categories."""
          category_count = {}

          for recipe in flat_recipes:
            recipe_details = await cookidoo.get_recipe_details(recipe.id)
            for category in recipe_details.categories:
              category_name = category.name
              category_count[category_name] = category_count.get(category_name, 0) + 1

          sorted_categories = sorted(category_count.items(), key=lambda x: x[1], reverse=True)

          print(f"Top {top_n} recipe categories:")
          for i, (category, count) in enumerate(sorted_categories[:top_n], start=1):
            print(f"{i}. {category}: {count} recipes")

          return sorted_categories[:top_n]


        async def process_recipes(cookidoo):
          """Process recipes and print statistics."""
          first_cooking_date = datetime(2025, 1, 1).date()
          flat_recipes = await get_all_recipes_since_date(cookidoo, first_cooking_date)
          # await count_total_recipes(flat_recipes, first_cooking_date)
          # await get_most_used_ingredients(cookidoo, flat_recipes)
          # await calculate_total_salt_usage(cookidoo, flat_recipes)
          # await calculate_total_cooking_time(cookidoo, flat_recipes)
          await get_top_recipe_categories(cookidoo, flat_recipes)


        # Call the function to process recipes
        await process_recipes(cookidoo)

asyncio.run(main())
