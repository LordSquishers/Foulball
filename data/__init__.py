import player

if player.PLAYER_DATA is None:
    # TODO- this will ALSO not work if there IS NO player file.
    player.PLAYER_DATA = player.load_player_file()
    print('Loaded Player Data!')