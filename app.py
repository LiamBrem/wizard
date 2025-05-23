import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import random
from pyFiles.deck import Deck, Card
from pyFiles.round import Round
from pyFiles.player import Player, ProbabilityPlayer, EvolvedPlayer, HumanPlayer
from pyFiles.genome import Genome
from pyFiles.simulation import prob_win, simulate_trick_outcome

# Set page config
st.set_page_config(
    page_title="Wizard Card Game Data Explorer",
    page_icon="🧙‍♂️",
    layout="wide"
)

# Initialize session state
if 'generated_data' not in st.session_state:
    st.session_state.generated_data = False
if 'player_comparison' not in st.session_state:
    st.session_state.player_comparison = None
if 'card_analysis' not in st.session_state:
    st.session_state.card_analysis = None
if 'game_outcomes' not in st.session_state:
    st.session_state.game_outcomes = None
if 'strategy_analysis' not in st.session_state:
    st.session_state.strategy_analysis = None
if 'deck' not in st.session_state:
    st.session_state.deck = Deck()
if 'hand' not in st.session_state:
    st.session_state.hand = []
if 'trump_suit' not in st.session_state:
    st.session_state.trump_suit = None
if 'trump_card' not in st.session_state:
    st.session_state.trump_card = None
if 'round_number' not in st.session_state:
    st.session_state.round_number = 5
if 'players' not in st.session_state:
    st.session_state.players = []
if 'game' not in st.session_state:
    st.session_state.game = None
if 'probabilities' not in st.session_state:
    st.session_state.probabilities = {}
if 'game_history' not in st.session_state:
    st.session_state.game_history = []
if 'random_hands' not in st.session_state:
    st.session_state.random_hands = None

# Helper functions
def card_to_emoji(card):
    if card.rank == 'W':
        return "🧙‍♂️"  # Wizard
    elif card.rank == 'E':
        return "🃏"  # Jester
    
    suit_emoji = {
        '♥': "♥️",
        '♦': "♦️",
        '♣': "♣️",
        '♠': "♠️",
        None: ""
    }
    
    return f"{card.rank}{suit_emoji.get(card.suit, '')}"

def card_to_color(card):
    if card.suit in ['♥', '♦']:
        return "red"
    elif card.suit in ['♣', '♠']:
        return "black"
    else:
        return "blue"  # For Wizard/Jester

def generate_random_hands(num_hands=100, hand_size=5):
    """Generate random hands and analyze them"""
    hands = []
    probabilities = []
    expected_tricks = []
    
    for _ in range(num_hands):
        deck = Deck()
        hand = deck.deal(hand_size)
        
        # Determine trump suit
        trump_card = deck.deal(1)[0] if deck.cards else None
        trump_suit = trump_card.suit if trump_card and trump_card.rank not in ('W', 'E') else None
        
        # Calculate probabilities
        hand_probs = [prob_win(card, hand, trump_suit, 4, hand_size) for card in hand]
        probabilities.append(hand_probs)
        expected_tricks.append(sum(hand_probs))
        
        # Store hand
        hands.append([str(card) for card in hand])
    
    # Create DataFrame
    df_hands = pd.DataFrame(hands)
    df_hands.columns = [f"Card {i+1}" for i in range(hand_size)]
    
    # Add probabilities
    df_probs = pd.DataFrame(probabilities)
    df_probs.columns = [f"Prob {i+1}" for i in range(hand_size)]
    
    # Add expected tricks
    df_hands['Expected Tricks'] = expected_tricks
    df_hands['Suggested Bid'] = [round(et) for et in expected_tricks]
    
    # Combine
    df = pd.concat([df_hands, df_probs], axis=1)
    
    return df

def compare_player_types(num_games=500):
    """Compare different player types across multiple games"""
    # Player types
    random_player = Player("Random")
    prob_player = ProbabilityPlayer("Probability")
    evolved_player = EvolvedPlayer("Evolved", Genome())
    
    players = [random_player, prob_player, evolved_player]
    results = []
    
    for game_num in range(num_games):
        # Create a new deck for each game
        deck = Deck()
        
        # Randomize round number (1-10)
        round_num = random.randint(1, 10)
        
        # Randomize number of players (3-6)
        num_players = random.randint(3, 6)
        
        for player_type in players:
            # Reset deck
            deck.reset()
            
            # Create a game with this player type and random opponents
            game_players = [player_type]
            for i in range(num_players - 1):
                game_players.append(Player(f"Opponent {i+1}"))
            
            # Create game
            game = Round([p.name for p in game_players], round_num)
            game.players = game_players
            
            # Deal cards
            for p in game_players:
                p.receive_cards(deck.deal(round_num))
            
            # Set trump
            if len(deck.cards) > 0:
                game.trump_card = deck.deal(1)[0]
                if game.trump_card.rank not in ('W', 'E'):
                    game.trump_suit = game.trump_card.suit
            
            # Play game
            game.collect_bids()
            game.play_tricks()
            
            # Record results
            scores = game.calculate_scores()
            
            # Get hand composition
            hand_composition = {
                'Wizards': sum(1 for c in game_players[0].hand if c.rank == 'W'),
                'Jesters': sum(1 for c in game_players[0].hand if c.rank == 'E'),
                'Trump': sum(1 for c in game_players[0].hand if c.suit == game.trump_suit and c.rank not in ('W', 'E')),
                'Non-Trump': sum(1 for c in game_players[0].hand if c.suit != game.trump_suit and c.rank not in ('W', 'E'))
            }
            
            results.append({
                'Game': game_num,
                'Player Type': player_type.name,
                'Round Number': round_num,
                'Num Players': num_players,
                'Bid': player_type.bid,
                'Tricks Won': player_type.tricks_won,
                'Score': scores[player_type.name],
                'Hit Bid': player_type.bid == player_type.tricks_won,
                'Wizards': hand_composition['Wizards'],
                'Jesters': hand_composition['Jesters'],
                'Trump Cards': hand_composition['Trump'],
                'Non-Trump Cards': hand_composition['Non-Trump'],
                'Trump Suit': game.trump_suit
            })
            
            # Reset player
            player_type.bid = 0
            player_type.tricks_won = 0
            player_type.hand = []
    
    return pd.DataFrame(results)

def analyze_card_effectiveness():
    """Analyze the effectiveness of different card types"""
    suits = ['♥', '♦', '♣', '♠']
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    
    # Create all possible cards
    all_cards = []
    
    # Add special cards
    all_cards.append(Card(None, 'W'))  # Wizard
    all_cards.append(Card(None, 'E'))  # Jester
    
    # Add regular cards
    for suit in suits:
        for rank in ranks:
            all_cards.append(Card(suit, rank))
    
    # Calculate win probabilities for different scenarios
    results = []
    
    # Scenarios: different number of players and different trump suits
    for num_players in [3, 4, 5, 6]:
        for trump_suit in [None] + suits:
            for card in all_cards:
                # Skip if card is the same suit as trump but we're checking "no trump"
                if trump_suit is None and card.suit is not None:
                    prob = prob_win(card, [], None, num_players, 10)
                    card_type = "Regular"
                elif card.rank == 'W':
                    prob = prob_win(card, [], trump_suit, num_players, 10)
                    card_type = "Wizard"
                elif card.rank == 'E':
                    prob = prob_win(card, [], trump_suit, num_players, 10)
                    card_type = "Jester"
                elif card.suit == trump_suit:
                    prob = prob_win(card, [], trump_suit, num_players, 10)
                    card_type = "Trump"
                else:
                    prob = prob_win(card, [], trump_suit, num_players, 10)
                    card_type = "Non-Trump"
                
                results.append({
                    'Card': str(card),
                    'Rank': card.rank,
                    'Suit': card.suit,
                    'Trump Suit': trump_suit,
                    'Num Players': num_players,
                    'Win Probability': prob,
                    'Card Type': card_type
                })
    
    return pd.DataFrame(results)

def analyze_game_outcomes(num_games=1000):
    """Analyze game outcomes based on different factors"""
    results = []
    
    for _ in range(num_games):
        # Create random game parameters
        num_players = random.randint(3, 6)
        round_num = random.randint(1, 10)
        
        # Create players
        players = [Player(f"Player {i+1}") for i in range(num_players)]
        
        # Create game
        game = Round([p.name for p in players], round_num)
        game.players = players
        
        # Play game
        game.setup_round()
        game.collect_bids()
        game.play_tricks()
        
        # Calculate scores
        scores = game.calculate_scores()
        
        # Record results for each player
        for player in players:
            # Calculate hand strength metrics
            wizards = sum(1 for c in player.hand if c.rank == 'W')
            jesters = sum(1 for c in player.hand if c.rank == 'E')
            trump_cards = sum(1 for c in player.hand if c.suit == game.trump_suit and c.rank not in ('W', 'E'))
            
            results.append({
                'Round Number': round_num,
                'Num Players': num_players,
                'Player': player.name,
                'Bid': player.bid,
                'Tricks Won': player.tricks_won,
                'Score': scores[player.name],
                'Hit Bid': player.bid == player.tricks_won,
                'Wizards': wizards,
                'Jesters': jesters,
                'Trump Cards': trump_cards,
                'Trump Suit': game.trump_suit
            })
    
    return pd.DataFrame(results)

def analyze_bidding_strategies():
    """Analyze different bidding strategies"""
    # Define different bidding strategies
    strategies = {
        "Conservative": lambda hand, trump_suit, num_players, round_num: max(0, round(sum(prob_win(c, hand, trump_suit, num_players, round_num) for c in hand) * 0.8)),
        "Aggressive": lambda hand, trump_suit, num_players, round_num: min(round_num, round(sum(prob_win(c, hand, trump_suit, num_players, round_num) for c in hand) * 1.2)),
        "Exact": lambda hand, trump_suit, num_players, round_num: round(sum(prob_win(c, hand, trump_suit, num_players, round_num) for c in hand)),
        "Zero": lambda hand, trump_suit, num_players, round_num: 0,
        "Max": lambda hand, trump_suit, num_players, round_num: round_num
    }
    
    results = []
    num_games = 500
    
    for _ in range(num_games):
        # Create random game parameters
        num_players = random.randint(3, 6)
        round_num = random.randint(1, 10)
        
        # Create deck
        deck = Deck()
        
        # For each strategy
        for strategy_name, bid_func in strategies.items():
            # Reset deck
            deck.reset()
            
            # Create players
            players = [Player(f"Player {i+1}") for i in range(num_players)]
            
            # Create game
            game = Round([p.name for p in players], round_num)
            game.players = players
            
            # Deal cards
            game.setup_round()
            
            # Override bid for player 0 based on strategy
            original_bid = players[0].bid
            players[0].bid = bid_func(players[0].hand, game.trump_suit, num_players, round_num)
            
            # Play game
            game.play_tricks()
            
            # Calculate scores
            scores = game.calculate_scores()
            
            # Record results for strategy player
            player = players[0]
            results.append({
                'Strategy': strategy_name,
                'Round Number': round_num,
                'Num Players': num_players,
                'Original Bid': original_bid,
                'Strategy Bid': player.bid,
                'Tricks Won': player.tricks_won,
                'Score': scores[player.name],
                'Hit Bid': player.bid == player.tricks_won,
                'Wizards': sum(1 for c in player.hand if c.rank == 'W'),
                'Jesters': sum(1 for c in player.hand if c.rank == 'E'),
                'Trump Cards': sum(1 for c in player.hand if c.suit == game.trump_suit and c.rank not in ('W', 'E'))
            })
    
    return pd.DataFrame(results)

def calculate_probabilities(hand, trump_suit, num_players):
    probabilities = {}
    for card in hand:
        prob = prob_win(card, hand, trump_suit, num_players, len(hand))
        probabilities[str(card)] = prob
    return probabilities

def deal_new_hand():
    # Reset the deck
    st.session_state.deck = Deck()
    
    # Get parameters
    round_number = st.session_state.round_number
    num_players = st.session_state.num_players
    
    # Deal cards
    st.session_state.hand = st.session_state.deck.deal(round_number)
    
    # Set trump card and suit
    if len(st.session_state.deck.cards) > 0:
        st.session_state.trump_card = st.session_state.deck.deal(1)[0]
        if st.session_state.trump_card.rank not in ('W', 'E'):
            st.session_state.trump_suit = st.session_state.trump_card.suit
        else:
            st.session_state.trump_suit = None
    else:
        st.session_state.trump_card = None
        st.session_state.trump_suit = None
    
    # Calculate probabilities
    st.session_state.probabilities = calculate_probabilities(
        st.session_state.hand, 
        st.session_state.trump_suit, 
        num_players
    )

def simulate_game():
    # Create players
    human_player = HumanPlayer("You")
    human_player.receive_cards(st.session_state.hand.copy())
    
    players = [human_player]
    for i in range(st.session_state.num_players - 1):
        if st.session_state.opponent_type == "Random":
            players.append(Player(f"Bot {i+1}"))
        elif st.session_state.opponent_type == "Probability":
            players.append(ProbabilityPlayer(f"ProbBot {i+1}"))
        else:  # Evolved
            genome = Genome()
            players.append(EvolvedPlayer(f"EvoBot {i+1}", genome))
    
    # Create game
    game = Round([p.name for p in players], st.session_state.round_number)
    game.players = players
    game.trump_card = st.session_state.trump_card
    game.trump_suit = st.session_state.trump_suit
    
    # Deal cards to other players
    for player in players[1:]:
        player.receive_cards(st.session_state.deck.deal(st.session_state.round_number))
    
    st.session_state.game = game
    st.session_state.players = players

def visualize_probabilities(probabilities):
    if not probabilities:
        return
    
    # Sort cards by probability
    sorted_cards = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)
    cards = [card for card, _ in sorted_cards]
    probs = [prob for _, prob in sorted_cards]
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 5))
    
    # Create bars with colors
    bars = ax.bar(cards, probs, color='skyblue')
    
    # Add labels and title
    ax.set_xlabel('Cards')
    ax.set_ylabel('Win Probability')
    ax.set_title('Probability of Winning a Trick with Each Card')
    ax.set_ylim(0, 1)
    
    # Add probability values on top of bars
    for bar, prob in zip(bars, probs):
        ax.text(
            bar.get_x() + bar.get_width()/2,
            bar.get_height() + 0.02,
            f'{prob:.2f}',
            ha='center',
            fontsize=9
        )
    
    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45)
    
    # Adjust layout
    plt.tight_layout()
    
    return fig

# Main app
st.title("🧙‍♂️ Wizard Card Game Data Explorer")
st.markdown("""
This application allows you to explore data and statistics about the Wizard card game.
Analyze card probabilities, player strategies, and game outcomes through interactive visualizations.
""")

# Sidebar for data generation
with st.sidebar:
    st.header("Data Generation")
    
    if st.button("Generate All Data"):
        with st.spinner("Generating data... This may take a minute."):
            st.session_state.player_comparison = compare_player_types(500)
            st.session_state.card_analysis = analyze_card_effectiveness()
            st.session_state.game_outcomes = analyze_game_outcomes(1000)
            st.session_state.strategy_analysis = analyze_bidding_strategies()
            st.session_state.generated_data = True
    
    st.markdown("---")
    
    st.markdown("""
    ### Card Types
    - 🧙‍♂️ **Wizard**: Always wins a trick
    - 🃏 **Jester**: Always loses a trick
    - **Trump**: Cards of the trump suit
    - **Regular**: Non-trump cards
    """)
    
    st.markdown("---")
    
    st.markdown("""
    ### Scoring Rules
    - If you win exactly the number of tricks you bid: 20 + 10 × bid
    - If you miss your bid: -10 × |tricks - bid|
    """)

# Main content
if not st.session_state.generated_data:
    st.info("Click 'Generate All Data' in the sidebar to start exploring.")
else:
    # Create tabs for different analyses
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Player Comparison", 
        "Card Analysis", 
        "Game Outcomes", 
        "Bidding Strategies",
        "Random Hand Generator"
    ])
    
    # Tab 1: Player Comparison
    with tab1:
        st.header("Player Type Comparison")
        st.markdown("""
        Compare how different player types perform across multiple games.
        - **Random**: Makes random bids and plays cards randomly
        - **Probability**: Uses probability calculations to make bids and play cards
        - **Evolved**: Uses a genome with weights for different strategies
        """)
        
        df = st.session_state.player_comparison
        
        # Summary statistics
        col1, col2 = st.columns(2)
        
        with col1:
            # Average score by player type
            avg_scores = df.groupby('Player Type')['Score'].mean().reset_index()
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.barplot(x='Player Type', y='Score', data=avg_scores, ax=ax)
            ax.set_title('Average Score by Player Type')
            ax.set_ylabel('Average Score')
            st.pyplot(fig)
            
            # Display summary table
            summary = df.groupby('Player Type').agg({
                'Score': 'mean',
                'Hit Bid': 'mean',
                'Bid': 'mean',
                'Tricks Won': 'mean'
            }).reset_index()
            
            summary = summary.rename(columns={
                'Score': 'Avg Score',
                'Hit Bid': 'Bid Accuracy',
                'Bid': 'Avg Bid',
                'Tricks Won': 'Avg Tricks'
            })
            
            # Format percentages
            summary['Bid Accuracy'] = summary['Bid Accuracy'].apply(lambda x: f"{x:.1%}")
            
            st.dataframe(summary)
        
        with col2:
            # Score distribution by player type
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.boxplot(x='Player Type', y='Score', data=df, ax=ax)
            ax.set_title('Score Distribution by Player Type')
            st.pyplot(fig)
            
            # Bid vs. Tricks Won
            fig, ax = plt.subplots(figsize=(10, 6))
            for player_type in df['Player Type'].unique():
                player_data = df[df['Player Type'] == player_type]
                ax.scatter(player_data['Bid'], player_data['Tricks Won'], alpha=0.5, label=player_type)
            
            # Add diagonal line (perfect bid)
            max_val = max(df['Bid'].max(), df['Tricks Won'].max()) + 1
            ax.plot([0, max_val], [0, max_val], 'k--', alpha=0.5)
            
            ax.set_xlabel('Bid')
            ax.set_ylabel('Tricks Won')
            ax.set_title('Bid vs. Tricks Won by Player Type')
            ax.legend()
            st.pyplot(fig)
        
        # Additional analysis
        st.subheader("Performance by Number of Players")
        
        # Player performance by number of players
        fig, ax = plt.subplots(figsize=(12, 6))
        sns.lineplot(x='Num Players', y='Score', hue='Player Type', data=df, marker='o', ci=None, ax=ax)
        ax.set_title('Average Score by Number of Players')
        ax.set_xlabel('Number of Players')
        ax.set_ylabel('Average Score')
        st.pyplot(fig)
        
        # Performance by round number
        st.subheader("Performance by Round Number")
        
        fig, ax = plt.subplots(figsize=(12, 6))
        sns.lineplot(x='Round Number', y='Score', hue='Player Type', data=df, marker='o', ci=None, ax=ax)
        ax.set_title('Average Score by Round Number')
        ax.set_xlabel('Round Number')
        ax.set_ylabel('Average Score')
        st.pyplot(fig)
        
        # Bid accuracy
        st.subheader("Bid Accuracy")
        
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(x='Player Type', y='Hit Bid', data=df, ax=ax)
        ax.set_title('Bid Accuracy by Player Type')
        ax.set_ylabel('Bid Accuracy Rate')
        ax.set_ylim(0, 1)
        st.pyplot(fig)
    
    # Tab 2: Card Analysis
    with tab2:
        st.header("Card Analysis")
        st.markdown("""
        Analyze the effectiveness of different card types across various game scenarios.
        """)
        
        df = st.session_state.card_analysis
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            selected_players = st.slider("Number of Players", min_value=3, max_value=6, value=4)
        
        with col2:
            trump_options = [None] + Deck.suits
            selected_trump = st.selectbox("Trump Suit", trump_options, format_func=lambda x: "None" if x is None else x)
        
        with col3:
            card_types = df['Card Type'].unique()
            selected_types = st.multiselect("Card Types", card_types, default=card_types)
        
        # Filter data
        filtered_df = df[
            (df['Num Players'] == selected_players) & 
            (df['Trump Suit'] == selected_trump) &
            (df['Card Type'].isin(selected_types))
        ]
        
        # Group by card type
        card_type_avg = filtered_df.groupby('Card Type')['Win Probability'].mean().reset_index()
        
        # Visualizations
        col1, col2 = st.columns(2)
        
        with col1:
            # Average win probability by card type
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.barplot(x='Card Type', y='Win Probability', data=card_type_avg, ax=ax)
            ax.set_title(f'Average Win Probability by Card Type\n({selected_players} Players, Trump: {selected_trump or "None"})')
            ax.set_ylim(0, 1)
            st.pyplot(fig)
        
        with col2:
            # Win probability by rank for regular cards
            regular_cards = filtered_df[filtered_df['Card Type'].isin(['Trump', 'Non-Trump'])]
            if not regular_cards.empty:
                # Convert rank to numeric for sorting
                rank_order = {r: i for i, r in enumerate(Deck.ranks)}
                regular_cards['Rank_Num'] = regular_cards['Rank'].map(rank_order)
                
                # Group by rank and card type
                rank_avg = regular_cards.groupby(['Rank', 'Card Type'])['Win Probability'].mean().reset_index()
                
                # Sort by rank
                rank_avg['Rank_Num'] = rank_avg['Rank'].map(rank_order)
                rank_avg = rank_avg.sort_values('Rank_Num')
                
                fig, ax = plt.subplots(figsize=(10, 6))
                sns.lineplot(x='Rank', y='Win Probability', hue='Card Type', data=rank_avg, marker='o', ax=ax)
                ax.set_title(f'Win Probability by Rank\n({selected_players} Players, Trump: {selected_trump or "None"})')
                ax.set_ylim(0, 1)
                plt.xticks(rotation=45)
                st.pyplot(fig)
        
        # Detailed card analysis
        st.subheader("Detailed Card Analysis")
        
        # Group by card and calculate average
        card_avg = filtered_df.groupby(['Card', 'Card Type'])['Win Probability'].mean().reset_index()
        card_avg = card_avg.sort_values('Win Probability', ascending=False)
        
        # Display top and bottom cards
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Top 10 Cards")
            top_cards = card_avg.head(10)
            
            # Create a bar chart
            fig, ax = plt.subplots(figsize=(10, 6))
            bars = ax.bar(top_cards['Card'], top_cards['Win Probability'])
            
            # Color bars by card type
            colors = {'Wizard': 'purple', 'Trump': 'red', 'Non-Trump': 'blue', 'Jester': 'green'}
            for i, bar in enumerate(bars):
                card_type = top_cards.iloc[i]['Card Type']
                bar.set_color(colors.get(card_type, 'gray'))
            
            ax.set_title('Top 10 Cards by Win Probability')
            ax.set_ylim(0, 1)
            plt.xticks(rotation=45)
            
            # Add legend
            from matplotlib.patches import Patch
            legend_elements = [Patch(facecolor=color, label=card_type) 
                              for card_type, color in colors.items()]
            ax.legend(handles=legend_elements)
            
            st.pyplot(fig)
        
        with col2:
            st.subheader("Bottom 10 Cards")
            bottom_cards = card_avg.tail(10)
            
            # Create a bar chart
            fig, ax = plt.subplots(figsize=(10, 6))
            bars = ax.bar(bottom_cards['Card'], bottom_cards['Win Probability'])
            
            # Color bars by card type
            for i, bar in enumerate(bars):
                card_type = bottom_cards.iloc[i]['Card Type']
                bar.set_color(colors.get(card_type, 'gray'))
            
            ax.set_title('Bottom 10 Cards by Win Probability')
            ax.set_ylim(0, 1)
            plt.xticks(rotation=45)
            
            # Add legend
            ax.legend(handles=legend_elements)
            
            st.pyplot(fig)
        
        # Full data table
        with st.expander("View Full Card Data"):
            st.dataframe(card_avg)
    
    # Tab 3: Game Outcomes
    with tab3:
        st.header("Game Outcomes Analysis")
        st.markdown("""
        Analyze how different factors affect game outcomes.
        """)
        
        df = st.session_state.game_outcomes
        
        # Summary statistics
        st.subheader("Factors Affecting Score")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Correlation between hand composition and score
            corr_data = df[['Score', 'Wizards', 'Jesters', 'Trump Cards']].corr()['Score'].drop('Score')
            
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.barplot(x=corr_data.index, y=corr_data.values, ax=ax)
            ax.set_title('Correlation with Score')
            ax.set_ylabel('Correlation Coefficient')
            st.pyplot(fig)
            
            # Average score by number of wizards
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.barplot(x='Wizards', y='Score', data=df, ax=ax)
            ax.set_title('Average Score by Number of Wizards')
            ax.set_xlabel('Number of Wizards')
            ax.set_ylabel('Average Score')
            st.pyplot(fig)
        
        with col2:
            # Average score by bid accuracy
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.barplot(x='Hit Bid', y='Score', data=df, ax=ax)
            ax.set_title('Average Score by Bid Accuracy')
            ax.set_xlabel('Hit Bid')
            ax.set_ylabel('Average Score')
            st.pyplot(fig)
            
            # Average score by number of trump cards
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.barplot(x='Trump Cards', y='Score', data=df, ax=ax)
            ax.set_title('Average Score by Number of Trump Cards')
            ax.set_xlabel('Number of Trump Cards')
            ax.set_ylabel('Average Score')
            st.pyplot(fig)
        
        # Bid vs. Tricks analysis
        st.subheader("Bid vs. Tricks Analysis")
        
        # Create a heatmap of bid vs. tricks
        bid_trick_counts = df.groupby(['Bid', 'Tricks Won']).size().reset_index(name='Count')
        
        # Create a pivot table
        pivot_data = bid_trick_counts.pivot(index='Bid', columns='Tricks Won', values='Count').fillna(0)
        
        fig, ax = plt.subplots(figsize=(12, 8))
        sns.heatmap(pivot_data, annot=True, fmt='.0f', cmap='YlGnBu', ax=ax)
        ax.set_title('Frequency of Bid vs. Tricks Won Combinations')
        ax.set_xlabel('Tricks Won')
        ax.set_ylabel('Bid')
        st.pyplot(fig)
        
        # Score distribution
        st.subheader("Score Distribution")
        
        fig, ax = plt.subplots(figsize=(12, 6))
        sns.histplot(df['Score'], bins=30, kde=True, ax=ax)
        ax.set_title('Distribution of Scores')
        ax.set_xlabel('Score')
        st.pyplot(fig)
        
        # Factors affecting bid accuracy
        st.subheader("Factors Affecting Bid Accuracy")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Bid accuracy by round number
            bid_accuracy = df.groupby('Round Number')['Hit Bid'].mean().reset_index()
            
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.lineplot(x='Round Number', y='Hit Bid', data=bid_accuracy, marker='o', ax=ax)
            ax.set_title('Bid Accuracy by Round Number')
            ax.set_xlabel('Round Number')
            ax.set_ylabel('Bid Accuracy Rate')
            ax.set_ylim(0, 1)
            st.pyplot(fig)
        
        with col2:
            # Bid accuracy by number of players
            bid_accuracy = df.groupby('Num Players')['Hit Bid'].mean().reset_index()
            
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.lineplot(x='Num Players', y='Hit Bid', data=bid_accuracy, marker='o', ax=ax)
            ax.set_title('Bid Accuracy by Number of Players')
            ax.set_xlabel('Number of Players')
            ax.set_ylabel('Bid Accuracy Rate')
            ax.set_ylim(0, 1)
            st.pyplot(fig)
    
    # Tab 4: Bidding Strategies
    with tab4:
        st.header("Bidding Strategy Analysis")
        st.markdown("""
        Compare different bidding strategies to see which performs best.
        
        - **Conservative**: Bids 80% of expected tricks
        - **Aggressive**: Bids 120% of expected tricks
        - **Exact**: Bids exactly the expected number of tricks
        - **Zero**: Always bids zero
        - **Max**: Always bids the maximum (round number)
        """)
        
        df = st.session_state.strategy_analysis
        
        # Summary statistics
        col1, col2 = st.columns(2)
        
        with col1:
            # Average score by strategy
            avg_scores = df.groupby('Strategy')['Score'].mean().reset_index()
            
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.barplot(x='Strategy', y='Score', data=avg_scores, ax=ax)
            ax.set_title('Average Score by Bidding Strategy')
            ax.set_ylabel('Average Score')
            st.pyplot(fig)
            
            # Display summary table
            summary = df.groupby('Strategy').agg({
                'Score': 'mean',
                'Hit Bid': 'mean',
                'Strategy Bid': 'mean',
                'Tricks Won': 'mean'
            }).reset_index()
            
            summary = summary.rename(columns={
                'Score': 'Avg Score',
                'Hit Bid': 'Bid Accuracy',
                'Strategy Bid': 'Avg Bid',
                'Tricks Won': 'Avg Tricks'
            })
            
            # Format percentages
            summary['Bid Accuracy'] = summary['Bid Accuracy'].apply(lambda x: f"{x:.1%}")
            
            st.dataframe(summary)
        
        with col2:
            # Score distribution by strategy
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.boxplot(x='Strategy', y='Score', data=df, ax=ax)
            ax.set_title('Score Distribution by Bidding Strategy')
            st.pyplot(fig)
            
            # Bid accuracy by strategy
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.barplot(x='Strategy', y='Hit Bid', data=df, ax=ax)
            ax.set_title('Bid Accuracy by Strategy')
            ax.set_ylabel('Bid Accuracy Rate')
            ax.set_ylim(0, 1)
            st.pyplot(fig)
        
        # Performance by round number
        st.subheader("Strategy Performance by Round Number")
        
        fig, ax = plt.subplots(figsize=(12, 6))
        sns.lineplot(x='Round Number', y='Score', hue='Strategy', data=df, marker='o', ci=None, ax=ax)
        ax.set_title('Average Score by Round Number')
        ax.set_xlabel('Round Number')
        ax.set_ylabel('Average Score')
        st.pyplot(fig)
        
        # Performance by hand composition
        st.subheader("Strategy Performance by Hand Composition")
        
        # Create hand strength metric
        df['Hand Strength'] = df['Wizards'] * 0.95 + df['Trump Cards'] * 0.7 - df['Jesters'] * 0.5
        
        # Bin hand strength
        df['Hand Strength Bin'] = pd.cut(df['Hand Strength'], bins=5, labels=['Very Weak', 'Weak', 'Average', 'Strong', 'Very Strong'])
        
        # Average score by hand strength and strategy
        hand_strength_scores = df.groupby(['Hand Strength Bin', 'Strategy'])['Score'].mean().reset_index()
        
        fig, ax = plt.subplots(figsize=(12, 8))
        sns.barplot(x='Hand Strength Bin', y='Score', hue='Strategy', data=hand_strength_scores, ax=ax)
        ax.set_title('Average Score by Hand Strength and Strategy')
        ax.set_xlabel('Hand Strength')
        ax.set_ylabel('Average Score')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        st.pyplot(fig)
        
        # Bid vs. Tricks analysis
        st.subheader("Bid vs. Tricks by Strategy")
        
        fig, ax = plt.subplots(figsize=(12, 8))
        for strategy in df['Strategy'].unique():
            strategy_data = df[df['Strategy'] == strategy]
            ax.scatter(strategy_data['Strategy Bid'], strategy_data['Tricks Won'], alpha=0.5, label=strategy)
        
        # Add diagonal line (perfect bid)
        max_val = max(df['Strategy Bid'].max(), df['Tricks Won'].max()) + 1
        ax.plot([0, max_val], [0, max_val], 'k--', alpha=0.5)
        
        ax.set_xlabel('Bid')
        ax.set_ylabel('Tricks Won')
        ax.set_title('Bid vs. Tricks Won by Strategy')
        ax.legend()
        st.pyplot(fig)
    
    # Tab 5: Random Hand Generator
    with tab5:
        st.header("Random Hand Generator")
        st.markdown("""
        Generate and analyze random hands to understand probabilities and optimal bidding.
        """)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            hand_size = st.slider("Hand Size", min_value=1, max_value=15, value=5)
        
        with col2:
            num_hands = st.slider("Number of Hands to Generate", min_value=10, max_value=1000, value=100)
        
        with col3:
            if st.button("Generate Hands"):
                with st.spinner("Generating hands..."):
                    random_hands = generate_random_hands(num_hands, hand_size)
                    st.session_state.random_hands = random_hands
        
        if 'random_hands' in st.session_state:
            # Display summary statistics
            df = st.session_state.random_hands
            
            st.subheader("Hand Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Distribution of expected tricks
                fig, ax = plt.subplots(figsize=(10, 6))
                sns.histplot(df['Expected Tricks'], bins=20, kde=True, ax=ax)
                ax.set_title('Distribution of Expected Tricks')
                ax.set_xlabel('Expected Tricks')
                st.pyplot(fig)
                
                # Average probability by card position
                prob_cols = [col for col in df.columns if col.startswith('Prob')]
                prob_means = [df[col].mean() for col in prob_cols]
                
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.bar(range(1, len(prob_means) + 1), prob_means)
                ax.set_title('Average Win Probability by Card Position')
                ax.set_xlabel('Card Position')
                ax.set_ylabel('Average Win Probability')
                ax.set_ylim(0, 1)
                st.pyplot(fig)
            
            with col2:
                # Distribution of suggested bids
                fig, ax = plt.subplots(figsize=(10, 6))
                sns.countplot(x='Suggested Bid', data=df, ax=ax)
                ax.set_title('Distribution of Suggested Bids')
                ax.set_xlabel('Suggested Bid')
                st.pyplot(fig)
                
                # Correlation between expected tricks and hand size
                if len(df) > 1:  # Need at least 2 points for correlation
                    correlation = df['Expected Tricks'].corr(df.index)
                    st.metric("Correlation between Expected Tricks and Hand Size", f"{correlation:.2f}")
            
            # Sample hands
            st.subheader("Sample Hands")
            
            # Sort by expected tricks
            df_sorted = df.sort_values('Expected Tricks', ascending=False)
            
            # Display top 5 hands
            st.subheader("Top 5 Hands (Highest Expected Tricks)")
            st.dataframe(df_sorted.head(5))
            
            # Display bottom 5 hands
            st.subheader("Bottom 5 Hands (Lowest Expected Tricks)")
            st.dataframe(df_sorted.tail(5))
            
            # Full data
            with st.expander("View All Generated Hands"):
                st.dataframe(df)

# Add footer
st.markdown("---")
st.markdown("Wizard Card Game Data Explorer | Created with Streamlit")
