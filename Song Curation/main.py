import librosa
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt
import os

def extract_mfcc(file_path, sr=44100, n_mfcc=13):
    """
    Extract MFCC features from an audio file.
    """
    try:
        y, _ = librosa.load(file_path, sr=sr)
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
        # Take the mean of each MFCC feature over time for compact representation
        mfcc_mean = np.mean(mfcc, axis=1)
        return mfcc_mean
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None

def compute_similarity_matrix(mfcc_features):
    """
    Compute a similarity matrix from MFCC features using cosine similarity.
    """
    return cosine_similarity(mfcc_features)

def plot_similarity_matrix(similarity_matrix, song_files):
    """
    Plot the similarity matrix as a heatmap.
    """
    plt.figure(figsize=(10, 8))
    plt.imshow(similarity_matrix, interpolation='nearest', cmap='coolwarm')
    plt.colorbar(label='Similarity Score')
    plt.title("Song Similarity Matrix")
    plt.xticks(ticks=np.arange(len(song_files)), labels=[os.path.basename(f) for f in song_files], rotation=90)
    plt.yticks(ticks=np.arange(len(song_files)), labels=[os.path.basename(f) for f in song_files])
    plt.tight_layout()
    plt.show()

def filter_outliers(similarity_matrix, song_files, threshold_factor=0.8):
    """
    Filter out songs that are not sufficiently similar to others in the pool.
    """
    # Compute the average similarity for each song
    avg_similarities = np.mean(similarity_matrix, axis=1)
    
    # Set a threshold for outlier removal (e.g., threshold_factor * mean similarity)
    threshold = threshold_factor * np.mean(avg_similarities)
    print(f"Threshold for similarity: {threshold:.2f}")
    
    # Keep only songs whose average similarity meets or exceeds the threshold
    filtered_songs = [
        (song_files[i], avg_similarities[i]) for i in range(len(song_files)) 
        if avg_similarities[i] >= threshold
    ]
    
    return filtered_songs

def main(song_files):
    """
    Main function to process songs and compute similarity.
    """
    print("Extracting MFCC features...")
    mfcc_features = []
    for file in song_files:
        mfcc = extract_mfcc(file)
        if mfcc is not None:
            mfcc_features.append(mfcc)
        else:
            print(f"Skipping {file} due to extraction error.")

    if len(mfcc_features) < 2:
        print("Not enough valid songs to compare.")
        return

    print("Computing similarity matrix...")
    similarity_matrix = compute_similarity_matrix(mfcc_features)

    print("Filtering outliers...")
    threshold_factor = 0.98  # Adjust this to change strictness of the filtering
    filtered_songs = filter_outliers(similarity_matrix, song_files, threshold_factor)

    if filtered_songs:
        print("Songs retained after filtering:")
        for song, avg_similarity in filtered_songs:
            print(f"- {os.path.basename(song)} (Average Similarity: {avg_similarity:.2f})")
    else:
        print("No songs retained after filtering.")

    print("Plotting similarity matrix...")
    plot_similarity_matrix(similarity_matrix, song_files)




# List of 10 song file paths
song_files = [
    "Songs/21 Savage Redrum Official Audio.mp3",
"Songs/A Bar Song Tipsy.mp3",
"Songs/Ariana Grande We Can't Be Friends.mp3",
"Songs/Belong Together Lyric Video.mp3",
"Songs/Benson Boone Beautiful Things Lyric Video.mp3",
"Songs/Benson Boone Slow It Down Lyrics.mp3",
"Songs/Beyoncé Texas Hold 'Em Visualizer.mp3",
"Songs/Billie Eilish Birds of a Feather.mp3",
"Songs/Billie Eilish Lunch Lyric Video.mp3",
"Songs/Chappell Roan - Good Luck Babe Official Lyric Video.mp3",
"Songs/Cruel Summer Taylor Swift.mp3",
"Songs/Dasha Austin Official Lyric Video.mp3",
"Songs/Die With A Smile Lyrics - Lady Gaga Bruno Mars.mp3",
"Songs/Djo End Of Beginning Official Audio.mp3",
"Songs/Don't Stop Believin Lyrics.mp3",
"Songs/Evergreen 4.mp3",
"Songs/Fast Car Lyrics - Luke Combs.mp3",
"Songs/Houdini 4.mp3",
"Songs/Hozier Too Sweet.mp3",
"Songs/I Like The Way You Kiss Me - Official Music Video.mp3",
"Songs/Like That - Metro Boomin Kendrick Lamar.mp3",
"Songs/Lovin On Me.mp3",
"Songs/Luke Combs Where the Wild Things Are.mp3",
"Songs/Miley Cyrus Flowers Lyric Video.mp3",
"Songs/Million Dollar Baby Tommy Richman.mp3",
"Songs/Mitski My Love Mine All Mine Lyric Video.mp3",
"Songs/Morgan Wallen Cowgirls ft ERNEST.mp3",
"Songs/Morgan Wallen Last Night Lyric Video.mp3",
"Songs/Morgan Wallen Thinkin Bout Me.mp3",
"Songs/Morgan Wallen You Proof Lyric Video.mp3",
"Songs/Myles Smith Stargazing Lyric Video.mp3",
"Songs/Noah Kahan Stick Season Lyric Video.mp3",
"Songs/Not Like Us 4.mp3",
"Songs/One Of The Girls - The Weeknd JENNIE Lily Rose Depp.mp3",
"Songs/Post Malone I Had Some Help ft Morgan Wallen.mp3",
"Songs/Riptide Lyrics Vance Joy.mp3",
"Songs/Sabrina Carpenter Espresso Official Audio.mp3",
"Songs/Sabrina Carpenter Please Please Please Lyric Video.mp3",
"Songs/Scared To Start Lyric Video.mp3",
"Songs/Sweater Weather.mp3",
"Songs/SZA Saturn 4.mp3",
"Songs/Tate McRae Greedy Lyrics.mp3",
"Songs/Taylor Swift Fortnight feat Post Malone.mp3",
"Songs/Teddy Swims Lose Control Lyric Video.mp3",
"Songs/Travis Scott FE!N ft Playboi Carti.mp3",
"Songs/Ty Dolla $ign CARNIVAL ft. Playboi Carti & Rich The Kid.mp3",
"Songs/Zach Bryan Heading South Lyrics.mp3",
"Songs/Zach Bryan Pink Skies.mp3",
"Songs/Zach Bryan Something In The Orange Lyrics.mp3",
]

# Run the program
if __name__ == "__main__":
    main(song_files)
