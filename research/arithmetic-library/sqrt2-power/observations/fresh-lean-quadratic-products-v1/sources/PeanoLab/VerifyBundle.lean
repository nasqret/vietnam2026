import PeanoLab.ProofBundle

namespace PeanoLab

/-- Verify self-contained canonical bundles in a process independent of Python. -/
def verifyBundleFile (path : String) : IO UInt32 := do
  let input ← IO.FS.readFile path
  match decodeBundleArtifactCanonical input with
  | .error message =>
      IO.eprintln s!"DECODE_ERROR\t{path}\t{message}"
      return 2
  | .ok artifact =>
      if artifact.check then
        IO.println
          s!"ACCEPT\t{path}\tnodes={artifact.bundle.nodes.length}\troot={artifact.bundle.root}"
        return 0
      else
        IO.println s!"REJECT\t{path}"
        return 1

def verifyBundleFiles : List String → IO UInt32
  | [] => return 0
  | path :: paths => do
      let status ← verifyBundleFile path
      let remaining ← verifyBundleFiles paths
      return max status remaining

end PeanoLab

def main (args : List String) : IO UInt32 := do
  match args with
  | [] =>
      IO.eprintln "usage: peano_lab_bundle_verify CANONICAL_BUNDLE.json [...]"
      return 64
  | paths => PeanoLab.verifyBundleFiles paths
