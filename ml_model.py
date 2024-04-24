import pickle
def predict_with_saved_model(data, model_filename='random_forest_model.pkl'):
   # Load the model from the pickle file
  loaded_model = pickle.load(open(model_filename, 'rb'))

  # Make predictions on the data
  predictions = loaded_model.predict(data)

  return predictions