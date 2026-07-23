from random import shuffle
from os import system,path,name

SCRIPT_DIR = path.dirname(path.abspath(__file__))
BANKROLL_FILE = path.join(SCRIPT_DIR, "blackjack_bankroll.txt")

def load_bankroll():
    if path.exists(BANKROLL_FILE):
        try:
            with open(BANKROLL_FILE, "r") as f:
                return int(f.read().strip())
        except (ValueError, IOError):
            return 1000
    return 1000

class BlackjackShoe:
    def __init__(self,decks=6):
        self.num_decks=decks
        self.reshuffle()

    def reshuffle(self):
        self.cards=[1,2,3,4,5,6,7,8,9,10,10,10,10]*4*self.num_decks
        shuffle(self.cards)

        self.running_count=0
        self.cut_card=int(len(self.cards)*0.25)
        print("\n*Dealer reshuffles the shoe*\n")

    @property
    def decks_remaining(self):
        return len(self.cards)/52

    @property
    def true_count(self):
        if self.decks_remaining>0:
            return self.running_count/self.decks_remaining
        return 0

    @property
    def needs_reshuffle(self):
        return len(self.cards)<=self.cut_card

    def draw(self):
        if not self.cards:
            self.reshuffle()

        card=self.cards.pop()

        if card in (2,3,4,5,6):
            self.running_count+=1
        elif card in (10,1):
            self.running_count-=1
        return card

class Hand:
    def __init__(self):
        self.cards = []

    def __str__(self):
        return f"{('Soft ' if self.is_soft else '')}{self.total}"

    def display(self, show_pair=True):
        if (
            show_pair
            and len(self.cards)==2
            and self.cards[0]==self.cards[1]
        ):
            return f"Pair of {self.cards[0] if self.cards[0]!=1 else 'Ace'}s"

        return str(self)
    def add_card(self, card):
        self.cards.append(card)
    
    @property
    def _evaluation(self):
        hard_total = sum(self.cards)

        total = hard_total
        soft = False

        if 1 in self.cards and total + 10 <= 21:
            total += 10
            soft = True

        return total, soft

    @property
    def total(self):
        return self._evaluation[0]
    
    @property
    def is_soft(self):
        return self._evaluation[1]
    
    def is_blackjack(self):
        return len(self.cards) == 2 and self.total == 21

    def is_bust(self):
        return self.total > 21
class Round:
    def __init__(self, bet):
        self.player_bets=[bet]
        self.player_hands = [Hand()]
        #self.player_blackjacks=[False]
        self.active_hand_index = 0
        self.dealer = Hand()

        #self.finished = False
        self.player_surrenders = [False]
        
    @property
    def current_hand(self):
        return self.player_hands[self.active_hand_index]
class BlackjackGame:
    def __init__(self,shoe=None):
        self.bankroll = load_bankroll()
        if shoe is None:
            shoe = BlackjackShoe()
        self.shoe = shoe
        self.current_round = None

    def start_round(self):
        if self.shoe.needs_reshuffle:
            self.shoe.reshuffle()
        self.current_round = Round(self.get_bet())
        r=self.current_round
        self.bankroll-=r.player_bets[0]
        self.deal_initial_cards()
        if r.dealer.cards[0] == 1:
            self.offer_insurance()
        if r.dealer.is_blackjack():
            if r.player_hands[0].is_blackjack():
                print("Both you and the dealer have Blackjack! It's a push.")
                self.bankroll += r.player_bets[0]
            else:
                print(f"Dealer has Blackjack! You lose your main bet of {r.player_bets[0]}.")
            return False
        if r.player_hands[0].is_blackjack():
            print(f"You have Blackjack! You receive ${r.player_bets[0] * 2.5}!")
            self.bankroll += int(r.player_bets[0] * 2.5)
            return False
        return True
        

    def get_bet(self):
        if self.bankroll<=0:
            print("You went bankrupt. Game over.")
            self.save_bankroll()
            raise SystemExit

        while True:
            try:
                bet=int(input(f"You have ${self.bankroll}. How much do you want to bet? "))
            except ValueError:
                print("Invalid input, try again.")
                continue
            if bet>self.bankroll:
                print("You don't have that much, try again.")
                continue
            if bet<=0:
                print("Bet must be greater than 0, try again.")
                continue
            return bet
        

    def deal_initial_cards(self):
        r = self.current_round
        for _ in range(2):
            r.player_hands[0].add_card(self.shoe.draw())
            r.dealer.add_card(self.shoe.draw())

    def offer_insurance(self):
        print("Dealer's upcard is an Ace. Do you want to take insurance? (y/n) ",end="")
        if input().lower()=="y":
            max_insurance = self.current_round.player_bets[0] // 2
            if max_insurance == 0 or self.bankroll == 0:
                print("You don't have enough to take insurance.")
                return
            if max_insurance > self.bankroll:
                max_insurance = self.bankroll
            while True:
                try:
                    insurancebet=int(input(f"How much do you want to bet on insurance? (up to ${max_insurance}) "))
                except ValueError:
                    print("Invalid input,try again.")
                    continue
                if insurancebet>max_insurance:
                    print(f"You can't bet more than ${max_insurance} on insurance,try again.")
                    continue
                if insurancebet<=0:
                    print("Bet must be greater than 0,try again.")
                    continue
                break
            self.bankroll-=insurancebet
            if self.current_round.dealer.is_blackjack():
                print(f"Dealer has Blackjack! You win ${insurancebet*3} from insurance.")
                self.bankroll+=insurancebet*3
            else:
                print("Dealer does not have Blackjack. You lose your insurance bet.")
            

    def player_turn(self):
        r=self.current_round
        print(f"Dealer's upcard: {r.dealer.cards[0] if r.dealer.cards[0]!=1 else 'Ace'}")
        index=0
        while index<len(r.player_hands):
            hand=r.player_hands[index]
            while True:
                print(f"\nYour hand: {hand.display(True)}")
                action = input("Choose action: (h)it, (s)tand, (d)ouble down, s(p)lit, su(r)render: ").lower()
                if action not in ('h','s','d','p','r'):
                    print("Invalid action, try again.")
                    continue
                if action == 'h':
                    hand.add_card(self.shoe.draw())
                    if hand.is_bust():
                        print(f"You bust with {hand.display(False)}.")
                        break
                elif action == 's':
                    break
                elif action == 'd':
                    if len(r.player_hands[index].cards)>2:
                        print("You can only double down on your first two cards.")
                        continue
                    if self.bankroll < r.player_bets[index]:
                        print("You don't have enough to double down, try another action.")
                        continue
                    self.bankroll-=r.player_bets[index]
                    r.player_bets[index] *= 2
                    r.player_hands[index].add_card(self.shoe.draw())
                    if r.player_hands[index].is_bust():
                        print(f"You bust with {r.player_hands[index].display(False)} (total: {r.player_hands[index].total}).")
                    print(f"Doubled down to a {r.player_hands[index].display(False)}")
                    break
                elif action == 'p':
                    if len(r.player_hands[index].cards) != 2 or r.player_hands[index].cards[0] != r.player_hands[index].cards[1]:
                        print("You can only split pairs, try another action.")
                        continue
                    if self.bankroll < r.player_bets[index]:
                        print("You don't have enough to split, try another action.")
                        continue
                    self.bankroll-=r.player_bets[index]
                    temp_hands = [Hand(), Hand()]
                    temp_hands[0].add_card(r.player_hands[index].cards[0])
                    temp_hands[1].add_card(r.player_hands[index].cards[1])
                    temp_hands[0].add_card(self.shoe.draw())
                    temp_hands[1].add_card(self.shoe.draw())
                    r.player_hands=r.player_hands[:index]+temp_hands+r.player_hands[index+1:]
                    r.player_bets=r.player_bets[:index]+[r.player_bets[index]]*2+r.player_bets[index+1:]
                    r.player_surrenders=r.player_surrenders[:index]+[False]*2+r.player_surrenders[index+1:]
                    # Handle each hand separately (not implemented in this simplified version)
                    #print("Split functionality is not fully implemented in this simplified version.")
                    index-=1 #Allow immediate play of first new hand
                    break
                elif action == 'r':
                    if len(r.player_hands[index].cards)>2:
                        print("You can only surrender on your first two cards")
                        continue
                    r.player_surrenders[index] = True
                    print("You surrendered. You win back half your bet.")
                    self.bankroll += r.player_bets[index] // 2
                    
                    break
            index+=1

    def dealer_turn(self):
        r = self.current_round
        if all(r.player_surrenders) or all(hand.is_bust() for hand in r.player_hands):
            return
        print(f"\nDealer's hand: {r.dealer.display(False)}")
        while r.dealer.total < 17:
            r.dealer.add_card(self.shoe.draw())
            print(f"\nDealer's hand: {r.dealer.display(False)}")
        if r.dealer.is_bust():
            print("Dealer busts!")

    def resolve_round(self):
        r = self.current_round
        for ind,_ in enumerate(r.player_hands):
            if r.player_surrenders[ind]:
                continue
            if r.player_hands[ind].is_bust():
                print(f"You lose ${r.player_bets[ind]}.")
            elif r.dealer.is_bust():
                print(f"You win ${r.player_bets[ind]}!")
                self.bankroll += 2*r.player_bets[ind]
            elif r.player_hands[ind].total > r.dealer.total:
                print(f"You win ${r.player_bets[ind]}!")
                self.bankroll += 2*r.player_bets[ind]
            elif r.player_hands[ind].total < r.dealer.total:
                print(f"You lose ${r.player_bets[ind]}.")
            else:
                print("It's a push. Your bet is returned.")
                self.bankroll += r.player_bets[ind]
        

    def save_bankroll(self):
        try:
            with open(BANKROLL_FILE, "w") as f:
                f.write(str(self.bankroll))
        except IOError:
            print("Warning: Could not save bankroll.")
    def play_game(self):
        print("Welcome to Blackjack!")
        while True:
            if self.start_round():
                self.player_turn()
                self.dealer_turn()
                self.resolve_round()
            if self.bankroll<=0:
                print("You went bankrupt. Game over.")
                break
            self.save_bankroll()
            again=input("\nDo you want to play another round? (y/n) ")
            if again.lower()!="y":
                print(f"Thanks for playing! Final bankroll: ${self.bankroll}")
                break
            system("clear" if name=="posix" else "cls")
if __name__ == "__main__":
    game = BlackjackGame(BlackjackShoe(1))
    game.play_game()