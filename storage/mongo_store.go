package storage

import (
	"context"
	"errors"
	"fmt"

	"github.com/nankp236270/weiqi-go/game"
	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"
)

// MongoGameStore 是 GameStore 接口的 MongoDB 实现
type MongoGameStore struct {
	collection *mongo.Collection
}

// NewMongoGameStore 创建一个新的 MongoDB 存储实例
func NewMongoGameStore(collection *mongo.Collection) *MongoGameStore {
	return &MongoGameStore{
		collection: collection,
	}
}

// mongoGame 是存储在 MongoDB 中的文档结构
type mongoGame struct {
	ID    string     `bson:"_id"`
	State *game.Game `bson:"state"`
}

func (s *MongoGameStore) CreateGame(gameID string, g *game.Game) error {
	doc := mongoGame{
		ID:    gameID,
		State: g,
	}
	_, err := s.collection.InsertOne(context.TODO(), doc)
	return err
}

func (s *MongoGameStore) GetGame(gameID string) (*game.Game, error) {
	var doc mongoGame
	filter := bson.M{"_id": gameID}

	err := s.collection.FindOne(context.TODO(), filter).Decode(&doc)
	if err != nil {
		if errors.Is(err, mongo.ErrNoDocuments) {
			return nil, fmt.Errorf("game with ID %s not found", gameID)
		}

		return nil, err
	}
	return doc.State, nil
}

func (s *MongoGameStore) UpdateGame(gameID string, g *game.Game) error {
	doc := mongoGame{
		ID:    gameID,
		State: g,
	}
	filter := bson.M{"_id": gameID}

	res, err := s.collection.ReplaceOne(context.TODO(), filter, doc)
	if err != nil {
		return err
	}
	if res.MatchedCount == 0 {
		return fmt.Errorf("game with %s not found for updata", gameID)
	}
	return nil
}

func (s *MongoGameStore) GetGamesByPlayer(playerID string) ([]GameInfo, error) {
	filter := bson.M{
		"$or": []bson.M{
			{"state.player_black": playerID},
			{"state.player_white": playerID},
		},
	}

	cursor, err := s.collection.Find(context.TODO(), filter)
	if err != nil {
		return nil, err
	}
	defer cursor.Close(context.TODO())

	var games []GameInfo
	for cursor.Next(context.TODO()) {
		var doc mongoGame
		if err := cursor.Decode(&doc); err != nil {
			continue
		}
		games = append(games, GameInfo{
			ID:          doc.ID,
			PlayerBlack: doc.State.PlayerBlack,
			PlayerWhite: doc.State.PlayerWhite,
			Status:      doc.State.Status,
			IsAIGame:    doc.State.IsAIGame,
			NextPlayer:  doc.State.NextPlayer,
			GameOver:    doc.State.GameOver,
		})
	}

	return games, nil
}

func (s *MongoGameStore) GetWaitingGames() ([]GameInfo, error) {
	filter := bson.M{"state.status": game.GameStatusWaiting}

	cursor, err := s.collection.Find(context.TODO(), filter)
	if err != nil {
		return nil, err
	}
	defer cursor.Close(context.TODO())

	var games []GameInfo
	for cursor.Next(context.TODO()) {
		var doc mongoGame
		if err := cursor.Decode(&doc); err != nil {
			continue
		}
		games = append(games, GameInfo{
			ID:          doc.ID,
			PlayerBlack: doc.State.PlayerBlack,
			PlayerWhite: doc.State.PlayerWhite,
			Status:      doc.State.Status,
			IsAIGame:    doc.State.IsAIGame,
			NextPlayer:  doc.State.NextPlayer,
			GameOver:    doc.State.GameOver,
		})
	}

	return games, nil
}
