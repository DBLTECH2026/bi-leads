# 1) Compila con Maven (las pruebas se corren en local: necesitan el MongoDB de prueba)
FROM maven:3.9-eclipse-temurin-21 AS compilar
WORKDIR /app
COPY pom.xml .
RUN mvn -q -B dependency:go-offline
COPY src src
RUN mvn -q -B -DskipTests package

# 2) Imagen final: solo el JRE y el .jar
FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --from=compilar /app/target/bi-leads-api-*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-XX:MaxRAMPercentage=60", "-jar", "/app/app.jar"]
