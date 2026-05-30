
import pandas as pd
import os
from datetime import datetime

FEEDBACK_FILE = 'data/human_feedback.csv'

def collect_feedback(schedule_id, feedback_type, rating, comments=None):
    """
    Simulates collection of human feedback.
    feedback_type: 'explicit' (star rating) or 'implicit' (export/edit)
    rating: 0 to 100 scale
    """
    new_entry = {
        'Schedule_ID': schedule_id,
        'Feedback_Type': feedback_type,
        'Human_Score': rating,
        'Comments': comments,
        'Timestamp': datetime.now().isoformat(),
        'User_Weight': 5.0 if feedback_type == 'explicit' else 2.0
    }
    
    df = pd.DataFrame([new_entry])
    if os.path.exists(FEEDBACK_FILE):
        df.to_csv(FEEDBACK_FILE, mode='a', header=False, index=False)
    else:
        df.to_csv(FEEDBACK_FILE, index=False)
    print(f"Feedback logged for {schedule_id}")

def merge_feedback_for_retraining(bootstrap_df, feedback_df):
    """
    Merges synthetic bootstrap data with high-weight human feedback.
    """
    # Assume bootstrap data has weight 1.0
    if 'User_Weight' not in bootstrap_df.columns:
        bootstrap_df['User_Weight'] = 1.0
        
    # In a real scenario, we'd join feedback with the actual schedule sessions.
    # For this architecture demo, we append the human-scored schedules.
    combined_df = pd.concat([bootstrap_df, feedback_df], ignore_index=True)
    return combined_df

if __name__ == "__main__":
    # Example usage
    collect_feedback('ver_42', 'explicit', 95.0, 'Perfect teacher distribution')
