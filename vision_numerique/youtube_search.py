from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError
import cv2


def search_config() :
    print("\nAvertissement : pour pouvoir faire une recherche Youtube sur tout le contenu possible vous devez vous connecter à votre compte Youtube (Google) depuis Firefox ou Google Chrome...")

    choice = str(input("\nCompte Youtube connecté ? [y/n] : "))

    search_opts = {}
    browser = None

    if choice == 'y' :
        while True:
            try:
                print("\nSélectionner le navigateur utilisé pour la connexion à votre compte Youtube : \n\t1) Firefox \n\t2) Chrome")

                browser_choice = int(input("\nChoix : "))
                assert browser_choice in (1, 2)

                browser = "firefox" if browser_choice == 1 else "chrome"

                break

            except AssertionError:
                print("Erreur, saisie incorrecte !")

        if browser :
            search_opts = {
                "cookiesfrombrowser": (browser, ),
                "format": "mp4",
                "quiet": True,
                "no_warnings": True
            }

    if not browser :
        search_opts = {
            "format": "mp4",
            "quiet": True,
            "no_warnings": True
        }

    return search_opts


def youtube_search() :
    # Recherche YouTube

    while True :
        query = str(input("\nRechercher une vidéo sur Youtube (titre, thème, ...) : "))

        search_str = f"ytsearch10:{query}"

        with YoutubeDL(ydl_opts) as ydl :
            try :
                print(f"\nRecherche de vidéos sur '{query}' en cours...")
                result = ydl.extract_info(search_str, download=False)

                print("\nVoici les 10 premiers résultats de la recherche :")

                for i, res in enumerate(result["entries"]) :
                    print(f"\t{i+1}) {res["title"]}")

                print("\n0) Quitter")

                video_choice = int(input("\nChoix : ")) - 1
                assert video_choice in range(-1, 10)

                if video_choice == -1 : return ""

                video = result['entries'][video_choice]
                video_url = video['webpage_url']

                break

            except DownloadError :
                print(f"\nErreur lors de la recherche de vidéos sur {query} !")


    # Téléchargement

    with YoutubeDL(ydl_opts) as ydl :
        print("\nDébut du téléchargement de la vidéo sélectionnée...\n")

        info = ydl.extract_info(video_url, download=True)
        video_path = ydl.prepare_filename(info)

        if video_path : print("\nTéléchargement de la vidéo effectué avec succès !")

    return video_path


ydl_opts = search_config()

if ydl_opts :
    video_path = youtube_search() # video_path pourra être utilisé avec MediaPipe

    # Lecture

    if video_path :
        cap = cv2.VideoCapture(video_path)

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            cv2.imshow("YouTube Video", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

