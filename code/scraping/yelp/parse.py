

if __name__ == '__main__':
    categories = []
    with open('restaurants.txt') as f:
        for line in f:
            temp = line.split(",")
            temp = temp[0].split("(")
            categories.append(temp[-1])
    print categories