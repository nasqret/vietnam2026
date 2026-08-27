import PeanoLab.Codec

namespace PeanoLab

def verifyFile (path : String) : IO UInt32 := do
  let input ← IO.FS.readFile path
  match decodeArtifactCanonical input with
  | .error message =>
      IO.eprintln s!"DECODE_ERROR\t{path}\t{message}"
      return 2
  | .ok artifact =>
      if artifact.check then
        IO.println s!"ACCEPT\t{path}\tfuel={artifact.fuel}"
        return 0
      else
        IO.println s!"REJECT\t{path}\tfuel={artifact.fuel}"
        return 1

def verifyFiles : List String -> IO UInt32
  | [] => return 0
  | path :: paths => do
      let status ← verifyFile path
      let rest ← verifyFiles paths
      return max status rest

end PeanoLab

def main (args : List String) : IO UInt32 := do
  match args with
  | [] =>
      IO.eprintln "usage: peano_lab_verify CANONICAL_ARTIFACT.json [...]"
      return 64
  | paths => PeanoLab.verifyFiles paths
