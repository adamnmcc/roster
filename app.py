from flask import Flask, render_template, request, redirect, url_for, send_file
import datetime
import random
import pandas as pd
import datetime
import random


app = Flask(__name__)

df_schedule = pd.DataFrame()

filename = "tournament_schedule.xlsx"

def generate_round_robin_teams(teams):
    if len(teams) % 2:
        teams.append(None)  # Add a dummy team for bye rounds if necessary
    rotation = list(teams)
    fixtures = []
    for i in range(len(teams) - 1):
        matches = []
        for j in range(len(teams) // 2):
            if rotation[j] is not None and rotation[len(teams) - 1 - j] is not None:
                if i % 2 == 0:
                    matches.append((rotation[j], rotation[len(teams) - 1 - j]))
                else:
                    matches.append((rotation[len(teams) - 1 - j], rotation[j]))
        fixtures.extend(matches)
        rotation = [rotation[0]] + [rotation[-1]] + rotation[1:-1]  # Rotate the list
    return fixtures

def schedule_matches(matches, start_time, game_length, changeover_time, end_time):
    pitch1 = start_time
    pitch2 = start_time
    last_teams_pitch1 = set()
    last_teams_pitch2 = set()
    last_referee_pitch1 = None
    last_referee_pitch2 = None
    scheduled_matches = {'Pitch 1': [], 'Pitch 2': []}
    game_count = {team: 0 for team in set(team for match in matches for team in match if team is not None)}
    all_teams = list(game_count.keys())

    for match in matches:
        current_teams = set(match)
        # Ensure referees are also not repeating back-to-back on the same pitch
        available_referees_pitch1 = [team for team in all_teams if team not in current_teams and team != last_referee_pitch1]
        available_referees_pitch2 = [team for team in all_teams if team not in current_teams and team != last_referee_pitch2]
        referee_pitch1 = random.choice(available_referees_pitch1) if available_referees_pitch1 else None
        referee_pitch2 = random.choice(available_referees_pitch2) if available_referees_pitch2 else None

        # Decide which pitch to use, ensuring no team or referee works back-to-back on the same pitch
        if pitch1 <= pitch2 and not (current_teams & last_teams_pitch1):
            next_time = pitch1
            pitch1 += datetime.timedelta(minutes=game_length + changeover_time)
            if pitch1 > end_time:
                continue
            referee = referee_pitch1
            last_referee_pitch1 = referee
            scheduled_matches['Pitch 1'].append((match[0], match[1], referee, next_time.strftime("%Y-%m-%d %H:%M")))
            game_count[match[0]] += 1
            game_count[match[1]] += 1
            last_teams_pitch1 = current_teams
        elif not (current_teams & last_teams_pitch2):
            next_time = pitch2
            pitch2 += datetime.timedelta(minutes=game_length + changeover_time)
            if pitch2 > end_time:
                continue
            referee = referee_pitch2
            last_referee_pitch2 = referee
            scheduled_matches['Pitch 2'].append((match[0], match[1], referee, next_time.strftime("%Y-%m-%d %H:%M")))
            game_count[match[0]] += 1
            game_count[match[1]] += 1
            last_teams_pitch2 = current_teams
        else:
            # If both pitches would result in back-to-back games or referee duty for any team, skip this match in this round
            continue

    for pitch in scheduled_matches:
        for match in scheduled_matches[pitch]:
            print(pitch, match)
            pd.concat([df_schedule, pd.DataFrame([pitch,match[0],match[1],match[2],match[3]])], axis=1)
    df_schedule.to_excel(filename, index=False)
    print(df_schedule)
    

    return scheduled_matches, game_count

# This code assumes the correct setup of datetime and other Python elements outside of this snippet.




@app.route('/download')
def download():
    
    return send_file(filename, as_attachment=True, download_name=filename)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        teams = request.form['team_names'].split(',')
        start_time = datetime.datetime.fromisoformat(request.form['start_time'])
        end_time = start_time.replace(hour=14, minute=0)  # Tournament must end before 14:00
        game_length = int(request.form['game_length'])
        changeover_time = int(request.form['changeover_time'])

        matches = generate_round_robin_teams(teams)
        
        scheduled_matches, game_count = schedule_matches(matches, start_time, game_length, changeover_time, end_time)

        # excel_file_path = generate_excel(scheduled_matches)

        return render_template('schedule.html', scheduled_matches=scheduled_matches, game_count=game_count)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
