/* global AudioWorkletProcessor, registerProcessor */
// Copies each mic block to the main thread, which resamples and frames it, so one resampler serves every runtime.
/** The AudioWorklet processor `openMic` loads as `tavia-capture`. */
class TaviaCapture extends AudioWorkletProcessor {
  process(inputs) {
    const channel = inputs[0] && inputs[0][0]
    if (channel) this.port.postMessage(channel.slice(0))
    return true
  }
}

registerProcessor('tavia-capture', TaviaCapture)
