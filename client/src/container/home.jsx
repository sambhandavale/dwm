import React, { useEffect, useState } from "react";

// const categories = [
//     'Beverages', 'Bakery', 'Dairy', 'Canned food', 'Produce', 'Deli',
//     'Meat', 'Health & beauty care', 'Prepared food', 'Snacks', 'Seafood'
// ];

const Home = () => {
    const [season, setSeason] = useState(2);
    const [associations, setAssociations] = useState([]);
    const [highestFreqCategory, setHighestFreqCategory] = useState('');
    const [loading, setLoading] = useState(true);
    const [categories , setCategories] = useState([]);
    const [option, setOption] = useState("Layout");
    const [graphs, setGraphs] = useState(2);

    console.log(graphs);

    useEffect(() => {
        const fetchAssociations = async () => {
            setLoading(true);
            try {
                const response = await fetch(`http://127.0.0.1:5000/associations?season=${season}`);
                if (!response.ok) {
                    throw new Error("Network response was not ok");
                }
                const data = await response.json();
                setAssociations(data.associations);
                setHighestFreqCategory(data.most_frequent_item);
                setCategories(data.categories);
            } catch (error) {
                console.error("Error fetching associations:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchAssociations();
    }, [season]); // Fetch data whenever the season changes

    // Find top associated categories dynamically for the highest frequency category
    const topAssociates = associations
        .filter(([cat1, cat2]) => cat1 === highestFreqCategory || cat2 === highestFreqCategory)
        .map(([cat1, cat2]) => (cat1 === highestFreqCategory ? cat2 : cat1));

    // Collect all categories involved in associations
    const associatedCategories = new Set(
        associations.flat() // Flatten the nested arrays of associations
    );

    // Get remaining categories by excluding the highest frequency category and all associated categories
    const remainingCategories = categories.filter(cat => 
        cat !== highestFreqCategory && !associatedCategories.has(cat)
    );

    // Group other associated categories (those not related to the highest frequency category)
    const groupedAssociations = associations
        .filter(([cat1, cat2]) => cat1 !== highestFreqCategory && cat2 !== highestFreqCategory)
        .reduce((acc, [cat1, cat2]) => {
            if (!acc[cat1]) acc[cat1] = [cat1];
            if (!acc[cat1].includes(cat2)) acc[cat1].push(cat2);
            return acc;
        }, {});

    let currentRemaining = [...remainingCategories];

    // Prepare categories for s1: max 4 categories from groupedAssociations or remaining
    const s1Categories = Object.values(groupedAssociations).flat().slice(0, 4);
    if (s1Categories.length < 4) {
        s1Categories.push(...currentRemaining.slice(0, 4 - s1Categories.length));
        currentRemaining = currentRemaining.slice(4 - s1Categories.length);
    }

    // Remaining categories go to s4, limited to 4 categories
    const s4Categories = currentRemaining.slice(0, 4);

    // Limit s2 to 2 categories
    const s2Categories = topAssociates.slice(0, 2);

    return (
        <div className="analyzer">
            <nav>
                <div className="logo">Supermarket Analyzer</div>
                <div className="more">
                    <img src="/assets/database.svg" alt="" className="database" />
                    <img src="/assets/report.svg" alt="" className="report" />
                </div>
            </nav>
            <main>
                <div className="options">
                    <div className={`option ${option === "Layout" ? `active` : ""}`} onClick={()=> setOption("Layout")}>Layout</div>
                    <div className={`option ${option === "Graphs" ? `active` : ""}`} onClick={()=> setOption("Graphs")}>Graphs</div>
                </div>
                <div className="content">
                    <div className="seasons">
                        <div 
                            className={`season ${season === 2 ? 'active' : ''}`} 
                            onClick={() => {
                                setSeason(2);
                                setGraphs(2)}}>
                            Spring
                        </div>
                        <div 
                            className={`season ${season === 3 ? 'active' : ''}`} 
                            onClick={() => {
                                setSeason(3);
                                setGraphs(3)}}>
                            Summer
                        </div>
                        <div 
                            className={`season ${season === 4 ? 'active' : ''}`} 
                            onClick={() => {
                                setSeason(4);
                                setGraphs(4)}}>
                            Autumn
                        </div>
                        <div 
                            className={`season ${season === 1 ? 'active' : ''}`} 
                            onClick={() => {
                                setSeason(1);
                                setGraphs(1)}}>
                            Winter
                        </div>
                    </div>
                    {option === "Layout" ? (
                        <div className="layout">
                            {/* Left Section - s1 */}
                            <div className="col">
                                <div className="s1">
                                    {s1Categories.map((cat, index) => (
                                        <div key={index} className={`cat${index + 1} cat`}>{cat}</div>
                                    ))}
                                </div>
                                <div className="counter">Counter 1</div>
                            </div>

                            {/* Middle Section - s2 and s3 */}
                            <div className="col-mid">
                                <div className="s2">
                                    {s2Categories.length > 0 ? (
                                        s2Categories.map((associate, index) => (
                                            <div key={index} className={`cat${index + 5} cat`}>{associate}</div>
                                        ))
                                    ) : (
                                        currentRemaining.slice(0, 2).map((cat, index) => (
                                            <div key={index} className={`cat${index + 5} cat`}>{cat}</div>
                                        ))
                                    )}
                                </div>
                                <div className="s3">
                                    <div className="cat7">{highestFreqCategory}</div> {/* Highest frequency */}
                                </div>
                                <div className="entry">Entry</div>
                            </div>

                            {/* Right Section - s4 */}
                            <div className="col">
                                <div className="s4">
                                    {s4Categories.map((cat, index) => (
                                        <div key={index + 8} className={`cat${index + 8} cat`}>{cat}</div>
                                    ))}
                                </div>
                                <div className="counter">Counter 2</div>
                            </div>
                        </div> 
                    ) : option === "Graphs" ? (
                        <div className="graphs">
                            {
                                <img src={`assets/static/category_counts_${graphs}.png`} />
                            }
                        </div> 
                    ) : null}
                </div>
            </main>
        </div>
    );
};

export default Home;
