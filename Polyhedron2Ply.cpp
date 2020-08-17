#include <CGAL/Inverse_index.h>
#include <CGAL/Polyhedron_3.h>
 
typedef CGAL::Exact_predicates_inexact_constructions_kernel Kernel;
typedef CGAL::Polyhedron_3<Kernel> Polyhedron;
typedef typename Polyhedron::Vertex_const_iterator VCI;
typedef typename Polyhedron::Facet_const_iterator FCI;
typedef typename Polyhedron::Halfedge_around_facet_const_circulator HFCC;
 
void write(){
    Polyhedron poly;
 
    // Your polyhedron code ...
 
    std::filebuf fb;
    fb.open(outputFile, std::ios::out);
    std::ostream os(&fb);
 
    os << "ply\n"
       << "format ascii 1.0\n"
       << "element vertex " << poly.size_of_vertices() << "\n"
       << "property float x\n"
       << "property float y\n"
       << "property float z\n"
       << "element face " << poly.size_of_facets() << "\n"
       << "property list uchar int vertex_index\n"
       << "end_header\n";
 
    for (auto it = poly.vertices_begin(); it != poly.vertices_end(); it++){
        os << it->point().x() << " " << it->point().y() << " " << it->point().z() << std::endl;
    }
 
    typedef CGAL::Inverse_index<VCI> Index;
    Index index(poly.vertices_begin(), poly.vertices_end());
 
    for( FCI fi = poly.facets_begin(); fi != poly.facets_end(); ++fi) {
        HFCC hc = fi->facet_begin();
        HFCC hc_end = hc;
 
        os << circulator_size(hc) << " ";
        do {
            os << index[VCI(hc->vertex())] << " ";
            ++hc;
        } while( hc != hc_end);
 
        os << "\n";
    }
 
    fb.close();
}
