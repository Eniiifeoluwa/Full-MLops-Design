"""
Simple model training script.
Trains a basic classifier on the Iris dataset and saves it.
"""
import joblib
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

def train_model():
    """Train a simple Random Forest model on Iris dataset."""
    print("Loading dataset...")
    iris = load_iris()
    X, y = iris.data, iris.target
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    print("Training model...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=5,
        random_state=42
    )
    model.fit(X_train, y_train)
    
    # Evaluate
    train_acc = accuracy_score(y_train, model.predict(X_train))
    test_acc = accuracy_score(y_test, model.predict(X_test))
    
    print(f"\nModel Performance:")
    print(f"Training Accuracy: {train_acc:.3f}")
    print(f"Test Accuracy: {test_acc:.3f}")
    print("\nClassification Report:")
    print(classification_report(y_test, model.predict(X_test), 
                                target_names=iris.target_names))
    
    # Save model
    print("\nSaving model...")
    joblib.dump(model, 'app/model.joblib')
    print("Model saved to app/model.joblib")
    
    return model

if __name__ == "__main__":
    train_model()
