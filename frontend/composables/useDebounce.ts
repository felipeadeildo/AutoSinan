export const useDebounce = <T extends (...args: any[]) => any>(
  fn: T,
  delay: number
) => {
  const timeout = ref<NodeJS.Timeout | null>(null)

  return (...args: Parameters<T>): ReturnType<T> | void => {
    if (timeout.value) {
      clearTimeout(timeout.value)
    }
    timeout.value = setTimeout(() => {
      fn(...args)
    }, delay)
  }
}
