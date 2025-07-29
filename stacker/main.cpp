#include <opencv2/opencv.hpp>
#include <vector>
#include <algorithm>
#include <cmath>
#include <iostream>
#include <memory>
#include <set>

struct Star {
    cv::Point2f position;
    float brightness;
    int id;
};

struct Triangle {
    int star1, star2, star3;
    float side1, side2, side3;
    float angle1, angle2, angle3;
    
    Triangle(const Star& s1, const Star& s2, const Star& s3, int id1, int id2, int id3) 
        : star1(id1), star2(id2), star3(id3) {
        // Calcul des distances des côtés
        side1 = cv::norm(s1.position - s2.position);
        side2 = cv::norm(s2.position - s3.position);
        side3 = cv::norm(s3.position - s1.position);
        
        // Calcul des angles en utilisant la loi des cosinus
        angle1 = std::acos((side1*side1 + side3*side3 - side2*side2) / (2*side1*side3));
        angle2 = std::acos((side1*side1 + side2*side2 - side3*side3) / (2*side1*side2));
        angle3 = M_PI - angle1 - angle2;
    }
};

struct TriangleMatch {
    int refTriangle;
    int targetTriangle;
    float similarity;
};

struct TransformationParams {
    cv::Point2f translation;
    float rotation;
    float scale;
    cv::Mat homography;
    bool isValid;
    float quality;
};

class AstroImageStacker {
private:
    std::vector<cv::Mat> images;
    std::vector<std::vector<Star>> starCatalogs;
    std::vector<float> imageQualityScores;
    int referenceFrameIndex;
    
    // Paramètres de détection d'étoiles
    float starThreshold = 50.0f;
    int minStarArea = 3;
    int maxStarArea = 100;
    
    // Paramètres d'alignement
    float triangleSimilarityThreshold = 0.95f;
    int minTrianglesForAlignment = 5;
    float maxAlignmentError = 2.0f;

public:
    AstroImageStacker() : referenceFrameIndex(-1) {}
    
    // Chargement des images
    bool loadImages(const std::vector<std::string>& imagePaths) {
        images.clear();
        starCatalogs.clear();
        imageQualityScores.clear();
        
        for (const auto& path : imagePaths) {
            cv::Mat img = cv::imread(path, cv::IMREAD_GRAYSCALE);
            if (img.empty()) {
                std::cerr << "Erreur: Impossible de charger l'image " << path << std::endl;
                return false;
            }
            images.push_back(img);
        }
        
        std::cout << "Chargé " << images.size() << " images." << std::endl;
        return true;
    }
    
    // Détection des étoiles dans une image
    std::vector<Star> detectStars(const cv::Mat& image) {
        std::vector<Star> stars;
        
        // Préparation de l'image
        cv::Mat blurred, binary;
        cv::GaussianBlur(image, blurred, cv::Size(3, 3), 1.0);
        cv::threshold(blurred, binary, starThreshold, 255, cv::THRESH_BINARY);
        
        // Détection des contours
        std::vector<std::vector<cv::Point>> contours;
        cv::findContours(binary, contours, cv::RETR_EXTERNAL, cv::CHAIN_APPROX_SIMPLE);
        
        for (size_t i = 0; i < contours.size(); i++) {
            double area = cv::contourArea(contours[i]);
            if (area >= minStarArea && area <= maxStarArea) {
                // Calcul du centroïde pondéré par la luminosité
                cv::Moments moments = cv::moments(contours[i]);
                if (moments.m00 > 0) {
                    cv::Point2f center(moments.m10 / moments.m00, moments.m01 / moments.m00);
                    
                    // Calcul de la luminosité moyenne dans la région
                    cv::Rect boundingRect = cv::boundingRect(contours[i]);
                    cv::Mat starRegion = image(boundingRect);
                    cv::Scalar meanBrightness = cv::mean(starRegion);
                    
                    Star star;
                    star.position = center;
                    star.brightness = meanBrightness[0];
                    star.id = stars.size();
                    stars.push_back(star);
                }
            }
        }
        
        // Tri par luminosité décroissante
        std::sort(stars.begin(), stars.end(), 
                 [](const Star& a, const Star& b) { return a.brightness > b.brightness; });
        
        // Garde seulement les N étoiles les plus brillantes
        if (stars.size() > 100) {
            stars.resize(100);
        }
        
        return stars;
    }
    
    // Calcul du score de qualité d'une image
    float calculateImageQuality(const cv::Mat& image, const std::vector<Star>& stars) {
        if (stars.empty()) return 0.0f;
        
        // Score basé sur le nombre d'étoiles et leur netteté
        float starCount = static_cast<float>(stars.size());
        float avgBrightness = 0.0f;
        float sharpness = 0.0f;
        
        for (const auto& star : stars) {
            avgBrightness += star.brightness;
        }
        avgBrightness /= starCount;
        
        // Calcul de la netteté via le gradient de Sobel
        cv::Mat grad_x, grad_y, grad;
        cv::Sobel(image, grad_x, CV_16S, 1, 0, 3);
        cv::Sobel(image, grad_y, CV_16S, 0, 1, 3);
        cv::addWeighted(cv::abs(grad_x), 0.5, cv::abs(grad_y), 0.5, 0, grad);
        sharpness = cv::mean(grad)[0];
        
        return starCount * 0.4f + avgBrightness * 0.3f + sharpness * 0.3f;
    }
    
    // Génération des triangles à partir des étoiles
    std::vector<Triangle> generateTriangles(const std::vector<Star>& stars) {
        std::vector<Triangle> triangles;
        
        // Génère tous les triangles possibles (limité aux étoiles les plus brillantes)
        int maxStars = std::min(static_cast<int>(stars.size()), 50);
        for (int i = 0; i < maxStars - 2; i++) {
            for (int j = i + 1; j < maxStars - 1; j++) {
                for (int k = j + 1; k < maxStars; k++) {
                    Triangle triangle(stars[i], stars[j], stars[k], i, j, k);
                    
                    // Filtre les triangles trop petits ou trop allongés
                    float minSide = std::min({triangle.side1, triangle.side2, triangle.side3});
                    float maxSide = std::max({triangle.side1, triangle.side2, triangle.side3});
                    
                    if (minSide > 10.0f && maxSide / minSide < 10.0f) {
                        triangles.push_back(triangle);
                    }
                }
            }
        }
        
        return triangles;
    }
    
    // Correspondance des triangles entre deux images
    std::vector<TriangleMatch> matchTriangles(const std::vector<Triangle>& refTriangles,
                                            const std::vector<Triangle>& targetTriangles) {
        std::vector<TriangleMatch> matches;
        
        for (size_t i = 0; i < refTriangles.size(); i++) {
            for (size_t j = 0; j < targetTriangles.size(); j++) {
                float similarity = calculateTriangleSimilarity(refTriangles[i], targetTriangles[j]);
                
                if (similarity > triangleSimilarityThreshold) {
                    TriangleMatch match;
                    match.refTriangle = i;
                    match.targetTriangle = j;
                    match.similarity = similarity;
                    matches.push_back(match);
                }
            }
        }
        
        // Tri par similarité décroissante
        std::sort(matches.begin(), matches.end(),
                 [](const TriangleMatch& a, const TriangleMatch& b) { 
                     return a.similarity > b.similarity; 
                 });
        
        return matches;
    }
    
    // Calcul de la similarité entre deux triangles
    float calculateTriangleSimilarity(const Triangle& t1, const Triangle& t2) {
        // Normalise les côtés par le plus grand côté
        float t1_s1 = t1.side1 / std::max({t1.side1, t1.side2, t1.side3});
        float t1_s2 = t1.side2 / std::max({t1.side1, t1.side2, t1.side3});
        float t1_s3 = t1.side3 / std::max({t1.side1, t1.side2, t1.side3});
        
        float t2_s1 = t2.side1 / std::max({t2.side1, t2.side2, t2.side3});
        float t2_s2 = t2.side2 / std::max({t2.side1, t2.side2, t2.side3});
        float t2_s3 = t2.side3 / std::max({t2.side1, t2.side2, t2.side3});
        
        // Compare les ratios des côtés (invariant à l'échelle)
        std::vector<float> ratios1 = {t1_s1, t1_s2, t1_s3};
        std::vector<float> ratios2 = {t2_s1, t2_s2, t2_s3};
        
        std::sort(ratios1.begin(), ratios1.end());
        std::sort(ratios2.begin(), ratios2.end());
        
        float similarity = 0.0f;
        for (int i = 0; i < 3; i++) {
            similarity += 1.0f - std::abs(ratios1[i] - ratios2[i]);
        }
        
        return similarity / 3.0f;
    }
    
    // Calcul manuel d'une transformation affine par moindres carrés
    cv::Mat calculateAffineTransform(const std::vector<cv::Point2f>& srcPoints,
                                   const std::vector<cv::Point2f>& dstPoints) {
        if (srcPoints.size() < 3 || srcPoints.size() != dstPoints.size()) {
            return cv::Mat();
        }
        
        int n = srcPoints.size();
        
        // Construction du système d'équations Ax = b pour la transformation affine
        // [x' y' 1] = [x y 1] * [a b tx; c d ty; 0 0 1]
        cv::Mat A = cv::Mat::zeros(2 * n, 6, CV_64F);
        cv::Mat b = cv::Mat::zeros(2 * n, 1, CV_64F);
        
        for (int i = 0; i < n; i++) {
            // Équation pour x'
            A.at<double>(2*i, 0) = srcPoints[i].x;     // a
            A.at<double>(2*i, 1) = srcPoints[i].y;     // b
            A.at<double>(2*i, 4) = 1.0;                // tx
            b.at<double>(2*i, 0) = dstPoints[i].x;
            
            // Équation pour y'
            A.at<double>(2*i+1, 2) = srcPoints[i].x;   // c
            A.at<double>(2*i+1, 3) = srcPoints[i].y;   // d
            A.at<double>(2*i+1, 5) = 1.0;              // ty
            b.at<double>(2*i+1, 0) = dstPoints[i].y;
        }
        
        // Résolution par moindres carrés
        cv::Mat x;
        cv::solve(A, b, x, cv::DECOMP_SVD);
        
        // Construction de la matrice de transformation 2x3
        cv::Mat transform = cv::Mat::zeros(2, 3, CV_64F);
        transform.at<double>(0, 0) = x.at<double>(0, 0); // a
        transform.at<double>(0, 1) = x.at<double>(1, 0); // b
        transform.at<double>(0, 2) = x.at<double>(4, 0); // tx
        transform.at<double>(1, 0) = x.at<double>(2, 0); // c
        transform.at<double>(1, 1) = x.at<double>(3, 0); // d
        transform.at<double>(1, 2) = x.at<double>(5, 0); // ty
        
        return transform;
    }
    
    // Calcul d'une transformation de similarité (translation + rotation + échelle)
    cv::Mat calculateSimilarityTransform(const std::vector<cv::Point2f>& srcPoints,
                                       const std::vector<cv::Point2f>& dstPoints) {
        if (srcPoints.size() < 2 || srcPoints.size() != dstPoints.size()) {
            return cv::Mat();
        }
        
        // Calcul des centroïdes
        cv::Point2f srcCenter(0, 0), dstCenter(0, 0);
        for (size_t i = 0; i < srcPoints.size(); i++) {
            srcCenter += srcPoints[i];
            dstCenter += dstPoints[i];
        }
        srcCenter *= (1.0f / srcPoints.size());
        dstCenter *= (1.0f / dstPoints.size());
        
        // Centrage des points
        std::vector<cv::Point2f> srcCentered, dstCentered;
        for (size_t i = 0; i < srcPoints.size(); i++) {
            srcCentered.push_back(srcPoints[i] - srcCenter);
            dstCentered.push_back(dstPoints[i] - dstCenter);
        }
        
        // Calcul de l'échelle
        float srcScale = 0, dstScale = 0;
        for (size_t i = 0; i < srcCentered.size(); i++) {
            srcScale += cv::norm(srcCentered[i]);
            dstScale += cv::norm(dstCentered[i]);
        }
        
        if (srcScale == 0) return cv::Mat();
        float scale = dstScale / srcScale;
        
        // Calcul de la rotation
        float num = 0, den = 0;
        for (size_t i = 0; i < srcCentered.size(); i++) {
            num += srcCentered[i].x * dstCentered[i].y - srcCentered[i].y * dstCentered[i].x;
            den += srcCentered[i].x * dstCentered[i].x + srcCentered[i].y * dstCentered[i].y;
        }
        
        float angle = (den != 0) ? std::atan2(num, den) : 0;
        float cosA = std::cos(angle);
        float sinA = std::sin(angle);
        
        // Construction de la matrice de transformation
        cv::Mat transform = cv::Mat::zeros(2, 3, CV_64F);
        transform.at<double>(0, 0) = scale * cosA;
        transform.at<double>(0, 1) = -scale * sinA;
        transform.at<double>(1, 0) = scale * sinA;
        transform.at<double>(1, 1) = scale * cosA;
        
        // Calcul de la translation
        cv::Point2f rotatedCenter;
        rotatedCenter.x = scale * (cosA * srcCenter.x - sinA * srcCenter.y);
        rotatedCenter.y = scale * (sinA * srcCenter.x + cosA * srcCenter.y);
        
        transform.at<double>(0, 2) = dstCenter.x - rotatedCenter.x;
        transform.at<double>(1, 2) = dstCenter.y - rotatedCenter.y;
        
        return transform;
    }

    // Calcul des paramètres de transformation par moindres carrés
    TransformationParams calculateTransformation(const std::vector<Star>& refStars,
                                               const std::vector<Star>& targetStars,
                                               const std::vector<TriangleMatch>& matches,
                                               const std::vector<Triangle>& refTriangles,
                                               const std::vector<Triangle>& targetTriangles) {
        TransformationParams params;
        params.isValid = false;
        
        if (matches.size() < minTrianglesForAlignment) {
            return params;
        }
        
        // Collecte les points correspondants avec élimination des doublons
        std::vector<cv::Point2f> refPoints, targetPoints;
        std::set<std::pair<int, int>> usedPairs;
        
        for (const auto& match : matches) {
            const Triangle& refTri = refTriangles[match.refTriangle];
            const Triangle& targetTri = targetTriangles[match.targetTriangle];
            
            // Ajoute les correspondances de points en évitant les doublons
            std::vector<std::pair<int, int>> pairs = {
                {refTri.star1, targetTri.star1},
                {refTri.star2, targetTri.star2},
                {refTri.star3, targetTri.star3}
            };
            
            for (const auto& pair : pairs) {
                if (usedPairs.find(pair) == usedPairs.end()) {
                    refPoints.push_back(refStars[pair.first].position);
                    targetPoints.push_back(targetStars[pair.second].position);
                    usedPairs.insert(pair);
                }
            }
        }
        
        if (refPoints.size() < 3) {
            return params;
        }
        
        cv::Mat transform;
        
        // Choix de la transformation selon le nombre d'étoiles
        if (refPoints.size() >= 6) {
            // Transformation affine complète
            transform = calculateAffineTransform(targetPoints, refPoints);
        } else {
            // Transformation de similarité (rotation + translation + échelle)
            transform = calculateSimilarityTransform(targetPoints, refPoints);
        }
        
        if (!transform.empty()) {
            // Conversion en matrice homogène 3x3
            params.homography = cv::Mat::eye(3, 3, CV_64F);
            transform.copyTo(params.homography(cv::Rect(0, 0, 3, 2)));
            params.isValid = true;
            
            // Calcul de la qualité de l'alignement
            params.quality = calculateAlignmentQuality(refPoints, targetPoints, params.homography);
        }
        
        return params;
    }
    
    // Calcul de la qualité de l'alignement
    float calculateAlignmentQuality(const std::vector<cv::Point2f>& refPoints,
                                  const std::vector<cv::Point2f>& targetPoints,
                                  const cv::Mat& homography) {
        float totalError = 0.0f;
        int validPoints = 0;
        
        for (size_t i = 0; i < targetPoints.size(); i++) {
            // Transformation manuelle du point
            cv::Mat point = (cv::Mat_<double>(3, 1) << targetPoints[i].x, targetPoints[i].y, 1.0);
            cv::Mat transformedPoint = homography * point;
            
            // Conversion en coordonnées cartésiennes
            float x = transformedPoint.at<double>(0, 0) / transformedPoint.at<double>(2, 0);
            float y = transformedPoint.at<double>(1, 0) / transformedPoint.at<double>(2, 0);
            
            float error = std::sqrt((x - refPoints[i].x) * (x - refPoints[i].x) + 
                                  (y - refPoints[i].y) * (y - refPoints[i].y));
                                  
            if (error < maxAlignmentError) {
                totalError += error;
                validPoints++;
            }
        }
        
        return validPoints > 0 ? (maxAlignmentError - totalError / validPoints) / maxAlignmentError : 0.0f;
    }
    
    // Processus principal de stacking
    cv::Mat stackImages() {
        if (images.empty()) {
            std::cerr << "Aucune image chargée!" << std::endl;
            return cv::Mat();
        }
        
        std::cout << "Détection des étoiles..." << std::endl;
        
        // Détection des étoiles dans toutes les images
        for (size_t i = 0; i < images.size(); i++) {
            auto stars = detectStars(images[i]);
            starCatalogs.push_back(stars);
            
            float quality = calculateImageQuality(images[i], stars);
            imageQualityScores.push_back(quality);
            
            std::cout << "Image " << i << ": " << stars.size() << " étoiles, qualité: " 
                     << quality << std::endl;
        }
        
        // Sélection de l'image de référence (meilleure qualité)
        referenceFrameIndex = std::distance(imageQualityScores.begin(),
                                          std::max_element(imageQualityScores.begin(), 
                                                         imageQualityScores.end()));
        
        std::cout << "Image de référence: " << referenceFrameIndex << std::endl;
        
        // Génération des triangles pour l'image de référence
        auto refTriangles = generateTriangles(starCatalogs[referenceFrameIndex]);
        std::cout << "Triangles de référence générés: " << refTriangles.size() << std::endl;
        
        // Alignement et stacking
        cv::Mat stackedImage = cv::Mat::zeros(images[0].size(), CV_32F);
        cv::Mat weightMap = cv::Mat::zeros(images[0].size(), CV_32F);
        
        for (size_t i = 0; i < images.size(); i++) {
            cv::Mat alignedImage;
            
            if (i == referenceFrameIndex) {
                // Image de référence - pas d'alignement nécessaire
                images[i].convertTo(alignedImage, CV_32F);
            } else {
                // Alignement de l'image
                auto targetTriangles = generateTriangles(starCatalogs[i]);
                auto matches = matchTriangles(refTriangles, targetTriangles);
                
                std::cout << "Image " << i << ": " << matches.size() << " correspondances de triangles" << std::endl;
                
                auto transformation = calculateTransformation(
                    starCatalogs[referenceFrameIndex], starCatalogs[i], 
                    matches, refTriangles, targetTriangles);
                
                if (transformation.isValid) {
                    cv::Mat temp;
                    images[i].convertTo(temp, CV_32F);
                    cv::warpPerspective(temp, alignedImage, transformation.homography, 
                                      images[0].size(), cv::INTER_LINEAR);
                    
                    std::cout << "Image " << i << " alignée avec qualité: " 
                             << transformation.quality << std::endl;
                } else {
                    std::cout << "Échec de l'alignement pour l'image " << i << std::endl;
                    continue;
                }
            }
            
            // Ajout à la pile avec pondération par qualité
            float weight = imageQualityScores[i];
            stackedImage += alignedImage * weight;
            weightMap += weight;
        }
        
        // Normalisation finale
        cv::Mat result;
        cv::divide(stackedImage, weightMap, result);
        result.convertTo(result, CV_8U);
        
        return result;
    }
    
    // Sauvegarde du résultat
    bool saveResult(const cv::Mat& result, const std::string& outputPath) {
        return cv::imwrite(outputPath, result);
    }
};

// Fonction principale d'exemple
int main(int argc, char* argv[]) {
    if (argc < 3) {
        std::cout << "Usage: " << argv[0] << " <image1> <image2> ... <output>" << std::endl;
        return -1;
    }
    
    // Récupération des chemins d'images
    std::vector<std::string> imagePaths;
    for (int i = 1; i < argc - 1; i++) {
        imagePaths.push_back(argv[i]);
    }
    std::string outputPath = argv[argc - 1];
    
    // Création et utilisation du stacker
    AstroImageStacker stacker;
    
    if (!stacker.loadImages(imagePaths)) {
        return -1;
    }
    
    std::cout << "Début du stacking..." << std::endl;
    cv::Mat result = stacker.stackImages();
    
    if (result.empty()) {
        std::cerr << "Échec du stacking!" << std::endl;
        return -1;
    }
    
    if (stacker.saveResult(result, "result.jpg")) {
        std::cout << "Résultat sauvegardé: " << outputPath << std::endl;
    } else {
        std::cerr << "Erreur lors de la sauvegarde!" << std::endl;
        return -1;
    }
    
    return 0;
}