
source ~/.config/nushell/scripts/modules/formats/from-env.nu

# Converts the environment variables from
# a bash script into a record
def "from bash" [path: string] -> record {
  bash -c $". ($path) && env" | from env | reject "PWD"
}