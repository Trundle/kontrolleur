function kontrolleur_ctrl_r
  if history | python kontrolleur.py | read -zl execute cursor match
    commandline -rb $match
    commandline -f repaint
    commandline -C $cursor
    if test $execute = True
      commandline -f execute
    end
  else
    commandline -f repaint
  end
end


bind \cr kontrolleur_ctrl_r
