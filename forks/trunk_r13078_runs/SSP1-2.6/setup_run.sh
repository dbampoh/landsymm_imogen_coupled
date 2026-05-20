#  args setup_run_keal_with_scratch_lpj_work.sh:
#                                       <runname>      <maininsfile> \"all other ins files in quotes\"                              <grid>                           <inputmethod>  <nodelist> <nnodes> <keal|uc2> <appendqueue> <appendntasks> <runqueue> <cpu_per_node>"

setup_run_owl_with_scratch_lpj_work.sh $(basename $PWD) main.ins "crop.ins crop_n.ins global.ins global_soiln.ins landcover.ins crop_n_pftlist.simplePFT.remap10_g2p.ins crop_n_stlist.simplePFT.remap10_g2p.N0-60-200-1000.ins wetlandpfts.ins" gridlist_in_62892_and_climate.txt cfx "" 4 owl milan 8 milan 64
