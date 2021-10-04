from pathlib import Path
import pickle

def cached(file_name: str, cache_dir=Path(".cache")):
    def cached_wrapper(func):
        cache_path = Path(cache_dir)

        def cached_f(*args, **kwargs):
            try:
                with cache_path.joinpath(file_name).open("rb") as cache_file:
                    cf = pickle.load(cache_file)
                    return cf
            except (FileNotFoundError, EOFError):
                pass

            result = func(*args, **kwargs)

            cache_path.mkdir(parents=True, exist_ok=True)
            with cache_path.joinpath(file_name).open("wb") as cache_file:
                cf = result
                pickle.dump(cf, cache_file)

            return result

        return cached_f

    return cached_wrapper
