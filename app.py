from flask import Flask, request, jsonify
import pandas as pd
from flask_cors import CORS
import itertools
import matplotlib.pyplot as plt
import os

app = Flask(__name__)
CORS(app)

data = pd.read_json("./data.json")

# Normalize the transactions
normalized_data = pd.json_normalize(data['transactions'])

# Explode the items list into separate rows
# This creates a new row for each item in the items list
items_normalized = normalized_data.explode('items')

# Normalize the exploded items into separate columns
# This will flatten the 'items' column into separate columns
items_df = pd.json_normalize(items_normalized['items'])

# Combine both DataFrames without duplicating rows
df = pd.concat([items_normalized.drop(columns=['items']).reset_index(drop=True), items_df.reset_index(drop=True)], axis=1)

df['user_id'] = df['user_id'].astype('category').cat.codes

def get_season(date):
    month = pd.to_datetime(date).month
    if month in [12, 1, 2]:  # Winter
        return 'Winter'
    elif month in [3, 4, 5]:  # Spring
        return 'Spring'
    elif month in [6, 7, 8]:  # Summer
        return 'Summer'
    else:  # Fall/Autumn
        return 'Autumn'

df['season'] = df['date'].apply(get_season)
 
categories = df['category'].unique()
winter_data = df[df['season'] == "Winter"]
spring_data = df[df['season'] == "Spring"]
summer_data = df[df['season'] == "Summer"]
autumn_data = df[df['season'] == "Autumn"]

winter_itemsets = winter_data.groupby('user_id')['category'].apply(list).reset_index(name='items')
spring_itemsets = spring_data.groupby('user_id')['category'].apply(list).reset_index(name='items')
summer_itemsets = summer_data.groupby('user_id')['category'].apply(list).reset_index(name='items')
autumn_itemsets = autumn_data.groupby('user_id')['category'].apply(list).reset_index(name='items')

def generate_frequent_itemsets(season_data, min_support):
    def find_frequent_itemsets(current_freq_itemsets, itemset_length):
        categories = list(itertools.combinations(current_freq_itemsets, itemset_length))
        cand = {}
        freq_item = []

        for i in categories:
            cand[i] = 0
            for j in season_data["items"]:
                if all(item in j for item in i):
                    cand[i] += 1

        for item, count in cand.items():
            if count > min_support:
                freq_item.append(item)

        return freq_item

    # Step 1: Generate frequent 1-itemsets
    cand1 = {}
    freq1_item = []
    for i in categories:
        cand1[i] = 0
        for j in season_data["items"]:
            if i in j:
                cand1[i] += 1

    for i in cand1:
        if cand1[i] > min_support:
            freq1_item.append(i)

    all_freq_itemsets = [freq1_item]

    # Step 2: Generate higher-order itemsets
    itemset_length = 2
    while True:
        if not all_freq_itemsets[-1]:
            break
        new_freq_itemsets = find_frequent_itemsets(all_freq_itemsets[-1], itemset_length)
        all_freq_itemsets.append(new_freq_itemsets)
        itemset_length += 1

    # Print all frequent itemsets
    for idx, freq in enumerate(all_freq_itemsets):
        print(f"Frequent {idx + 1}-itemsets:", freq)

    return all_freq_itemsets

def calculate_support(itemset, winter_itemsets):
    count = 0
    for j in winter_itemsets["items"]:
        if all(item in j for item in itemset):
            count += 1
    return count

def generate_association_rules(frequent_itemsets, winter_itemsets, min_confidence):
    rules = []

    for itemset in frequent_itemsets:
        # Generate all possible non-empty subsets of the itemset
        for i in range(1, len(itemset)):
            antecedents = itertools.combinations(itemset, i)
            for antecedent in antecedents:
                # Create the consequent as the remaining items
                consequent = list(set(itemset) - set(antecedent))

                if consequent:  # Only proceed if there is a consequent
                    support_antecedent = calculate_support(antecedent, winter_itemsets)
                    support_both = calculate_support(antecedent + tuple(consequent), winter_itemsets)

                    if support_antecedent > 0:  # Prevent division by zero
                        confidence = support_both / support_antecedent
                        if confidence >= min_confidence:
                            rules.append((antecedent, consequent, support_both, confidence))

    return rules

def generate_category_graph(season, season_data):
    # Ensure the static directory exists
    static_dir = 'static'
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)

    category_counts = season_data["category"].value_counts()
    
    plt.figure(figsize=(5, 3))
    category_counts.plot(kind='bar', color='skyblue')
    plt.title(f'Category Counts for {get_season(season_data["date"].iloc[0])} Season')
    plt.xlabel('Category')
    plt.ylabel('Count')
    plt.xticks(rotation=45)
    plt.grid(axis='y')
    
    # Save the figure
    graph_path = os.path.join(f'assets/static/category_counts_{season}.png')
    plt.savefig(graph_path, bbox_inches='tight')
    plt.close()  # Close the figure to free up memory
    
    return graph_path

@app.route('/associations', methods=['GET'])
def get_associations():
    season = request.args.get('season', type=int)
    min_support = 10
    min_confidence = 0.5

    if season == 1:
        season_data = winter_itemsets
        freqseasondata = df[df['season'] == "Winter"]
    elif season == 2:
        season_data = spring_itemsets
        freqseasondata = df[df['season'] == "Spring"]
    elif season == 3:
        season_data = summer_itemsets
        freqseasondata = df[df['season'] == "Summer"]
    elif season == 4:
        season_data = autumn_itemsets
        freqseasondata = df[df['season'] == "Autumn"]
    else:
        return jsonify({"error": "Invalid season"}), 400
    
    # graph_path = generate_category_graph(season, freqseasondata)
    
    all_freq_itemsets = generate_frequent_itemsets(season_data, min_support)
    association_rules = generate_association_rules(all_freq_itemsets[1], winter_itemsets, min_confidence)

    assoc = []
    for i in association_rules:
        assoc.append([i[0][0], i[1][0]])

    # Get the most frequent item for the selected season
    most_frequent_item = freqseasondata['category'].value_counts().idxmax()
    categories = df['category'].unique().tolist()  # Convert to list

    return jsonify({
        "associations": assoc,
        "most_frequent_item": most_frequent_item,
        "categories": categories,
        # "graph_url": [graph_path],
    })

if __name__ == "__main__":
    app.run(debug=True)
