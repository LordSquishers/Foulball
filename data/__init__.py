import player

if player.PLAYER_DATA is None:
    player.PLAYER_DATA = player.load_player_file()
    print('Loaded Player Data!')