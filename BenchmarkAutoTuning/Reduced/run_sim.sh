#!/bin/bash

# In das Zielverzeichnis wechseln (bricht ab, falls der Pfad nicht existiert)
cd /home/larsd/dokumente/Master2/AutoPas/build/examples/md-flexible || exit 1

OUTPUT_FILE="simulation_results_5Runs.txt"

# Alte Ergebnisdatei leeren oder neu anlegen
> "$OUTPUT_FILE"

for i in {1..5}; do
    echo "Starting run $i of 5..."
    
    # Trennlinie in die Textdatei schreiben, um die Läufe auseinanderzuhalten
    echo "==========================================" >> "$OUTPUT_FILE"
    echo "RUN $i - $(date)" >> "$OUTPUT_FILE"
    echo "==========================================" >> "$OUTPUT_FILE"
    
    # Simulation starten und Standardausgabe (stdout) sowie Fehler (stderr) anhängen
    ./md-flexible --no-progress-bar --yaml-filename fallingDrop.yaml >> "$OUTPUT_FILE" 2>&1
    
    echo "" >> "$OUTPUT_FILE"
done

echo "Done! All results are stored in '$OUTPUT_FILE'."