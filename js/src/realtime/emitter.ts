type Listener = (...args: unknown[]) => void

/** A minimal typed event emitter; a throwing listener is logged and does not stop the others. */
export class Emitter<Events extends Record<string, unknown[]>> {
  private readonly listeners = new Map<keyof Events, Set<Listener>>()

  /** Adds a listener; returns a function that removes it. */
  on<K extends keyof Events>(name: K, cb: (...args: Events[K]) => void): () => void {
    const set = this.listeners.get(name) ?? new Set<Listener>()
    const fn = cb as unknown as Listener
    set.add(fn)
    this.listeners.set(name, set)
    return () => { set.delete(fn) }
  }

  /** Calls every listener of `name` with `args`. */
  emit<K extends keyof Events>(name: K, ...args: Events[K]): void {
    for (const cb of this.listeners.get(name) ?? []) {
      try {
        cb(...args)
      } catch (err) {
        console.error(err)
      }
    }
  }
}
