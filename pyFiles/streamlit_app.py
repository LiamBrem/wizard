# streamlit_app.py
import streamlit as st
import time
from round import Round
from player import Player, ProbabilityPlayer, EvolvedPlayer, HumanPlayer
from genome import Genome



# ── SESSION-STATE INITIALIZATION ────────────────────────────────────────────
if "phase" not in st.session_state:
    st.session_state.phase = "choose_bots"
if "players" not in st.session_state:
    st.session_state.players = []
if "round" not in st.session_state:
    st.session_state.round = None
if "bid_index" not in st.session_state:
    st.session_state.bid_index = 0
if "trick_index" not in st.session_state:
    st.session_state.trick_index = 0
if "current_trick" not in st.session_state:
    st.session_state.current_trick = []
if "current_round" not in st.session_state:
    st.session_state.current_round = None
if "max_rounds" not in st.session_state:
    st.session_state.max_rounds = None
if "cumulative_scores" not in st.session_state:
    st.session_state.cumulative_scores = {}
# ────────────────────────────────────────────────────────────────────────────


def init_state():
    if "phase" not in st.session_state:
        st.session_state.phase = "choose_bots"
    if "round" not in st.session_state:
        st.session_state.round = None
    if "players" not in st.session_state:
        st.session_state.players = []
    if "bid_index" not in st.session_state:
        st.session_state.bid_index = 0
    if "trick_index" not in st.session_state:
        st.session_state.trick_index = 0
    if "current_trick" not in st.session_state:
        st.session_state.current_trick = []


if st.session_state.phase == "choose_bots":
    human = HumanPlayer("You")
    n = st.slider("Number of total players", min_value=3, max_value=6, value=3, step=1)
    bot_types = []
    for i in range(n - 1):
        bot_types.append(
            st.selectbox(f"Bot #{i+1} type",
                         ["Random", "Probability", "Evolved"],
                         key=f"bot_type_{i}")
        )
    if st.button("Start Game"):
        # build players list
        bots = []
        for t in bot_types:
            if t == "Random":
                bots.append(Player(f"Bot{len(bots)+1}"))
            elif t == "Probability":
                bots.append(ProbabilityPlayer(f"ProbBot{len(bots)+1}"))
            else:
                # supply an existing genome dictionary
                genome = Genome({'high_card_weight': 0.4636924165136554, 'wizard_weight': 0.8298591867078169, 'jester_weight': -1.4333575259840647, 'trump_weight': 1.0385925650015846, 'position_bias': 0.14219460828580763, 'risk_bias': 0.6361510350440189, 'overbid_penalty_weight': 1.0819429179548399})
                bots.append(EvolvedPlayer(f"EvoBot{len(bots)+1}", genome))
        
        players = [human] + bots
        st.session_state.players = players

        # 1) compute how many rounds total
        total = len(players)
        st.session_state.max_rounds = 60 // total
        st.session_state.current_round = 1

        # 2) reset running totals
        st.session_state.cumulative_scores = {p.name: 0 for p in players}

        # 3) instantiate round 1
        st.session_state.round = Round(players, round_number=1)
        st.session_state.phase = "bidding"
        st.rerun()



elif st.session_state.phase == "bidding":
    if st.session_state.bid_index >= len(st.session_state.round.players):
        st.session_state.phase = "playing"
        st.rerun()

    r = st.session_state.round
    st.subheader(f"Round {st.session_state.current_round} of {st.session_state.max_rounds}")
    # run setup just once
    if r.trump_card is None:
        r.setup_round()

    p = st.session_state.players[st.session_state.bid_index]
    st.write(f"Trump: {r.trump_card} → {r.trump_suit}")
    if isinstance(p, HumanPlayer):
        bid = st.number_input("Your bid", 0, r.round_number, key="human_bid")
        if st.button("Confirm bid"):
            p.set_bid(bid)
            r.collect_bids()  # this will consume your pending bid
            st.session_state.bid_index += 1
            st.rerun()
    else:
        st.write(f"{p.name} is thinking…")
        time.sleep(1)  # one‐second pause
        b = p.make_bid(r.trump_suit, r.round_number,
                       st.session_state.bid_index,
                       len(r.players),
                       bids_so_far=r.get_bids().values())
        st.write(f"{p.name} bids **{b}**")
        st.session_state.bid_index += 1
        st.rerun()

    # once all bids taken:
    if st.session_state.bid_index >= len(r.players):
        st.session_state.phase = "playing"
        st.rerun()



elif st.session_state.phase == "playing":
    r = st.session_state.round
    st.subheader(f"Round {st.session_state.current_round} of {st.session_state.max_rounds}")


    # Display previous tricks
    played = r.get_played_cards()                  # flat list of Card
    n = len(st.session_state.players)              # number of players
    tricks = [played[i:i+n] for i in range(0, len(played), n)]

    st.write("### Tricks so far")
    for tnum, cards in enumerate(tricks, start=1):
        st.write(f"Trick {tnum}: " + ", ".join(map(str, cards)))

    # On each “turn” show whose turn it is
    idx = st.session_state.trick_index
    player = r.players[(r.leader_index + idx) % len(r.players)]
    st.write(f"**{player.name}** to play next.")

    legal = player.legal_cards(r.lead_suit)
    if isinstance(player, HumanPlayer):
        # 1) get the list of legal Card instances from the hand
        legal_cards = player.legal_cards(r.lead_suit)

        # 2) present the user with a choice of indices
        turn_key = f"choice_{st.session_state.current_round}_{r.trick_number}"
        choice_index = st.selectbox(
            "Select a card",
            options=list(range(len(legal_cards))),
            format_func=lambda i: str(legal_cards[i]),
            key=turn_key
        )

        if st.button("Play", key="btn_"+turn_key):
            # 3) pick out the real Card instance from legal_cards
            card_to_play = legal_cards[choice_index]
            player.set_card(card_to_play)
            r.play_card_for_player(player)

            # clean up and advance
            st.session_state.trick_index += 1
            # delete the widget state so we get a fresh selectbox next trick
            del st.session_state[turn_key]
            st.rerun()


    else:
        st.write(f"{player.name} is choosing a card…")
        time.sleep(1)
        card = player.play_card(r.current_trick, r.lead_suit,
                                r.trump_suit, r.played_cards)
        st.write(f"{player.name} plays **{card}**")
        r.current_trick.append((r.players.index(player), card))
        r.played_cards.append(card)
        if r.lead_suit is None and card.rank not in ("W", "E"):
            r.lead_suit = card.suit
        st.session_state.trick_index += 1
        st.rerun()

    # once everyone has played this trick:
    if r.is_trick_complete():
        winner = r.finish_trick()
        st.write(f"🏆 {winner} wins trick #{r.trick_number}")
        # reset indices for next trick
        st.session_state.trick_index = 0
        st.rerun()

    # after all tricks:
    if r.is_round_over():
        st.session_state.phase = "results"
        st.rerun()



elif st.session_state.phase == "results":
    r = st.session_state.round
    # per‐round scores
    round_scores = r.calculate_scores()
    st.write("### This Round’s Scores")
    for name, pts in round_scores.items():
        st.write(f"{name}: **{pts}**")

    # add into cumulative
    for name, pts in round_scores.items():
        st.session_state.cumulative_scores[name] += pts

    if st.session_state.current_round < st.session_state.max_rounds:
        if st.button("Next Round"):
            # advance
            st.session_state.current_round += 1
            st.session_state.bid_index = 0
            st.session_state.trick_index = 0
            st.session_state.phase = "bidding"
            # new Round with higher deal count
            st.session_state.round = Round(
                st.session_state.players,
                round_number=st.session_state.current_round
            )
            st.rerun()
    else:
        st.session_state.phase = "game_over"
        st.rerun()



elif st.session_state.phase == "game_over":
    st.header("🏁 Game Over – Final Scores")
    # sort descending
    final = sorted(
        st.session_state.cumulative_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )
    for name, total in final:
        st.write(f"{name}: **{total}**")

    if st.button("Play Again"):
        # reset to start‐up
        for key in [
            "phase", "players", "round", "bid_index",
            "trick_index", "current_trick",
            "current_round", "max_rounds", "cumulative_scores"
        ]:
            del st.session_state[key]
        st.experimental_rerun()
